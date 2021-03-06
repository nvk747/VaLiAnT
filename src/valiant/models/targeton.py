########## LICENCE ##########
# VaLiAnT, (c) 2020, GRL (the "Software")
# 
# The Software remains the property of Genome Research Ltd ("GRL").
# 
# The Software is distributed "AS IS" under this Licence solely for non-commercial use in the hope that it will be useful,
# but in order that GRL as a charitable foundation protects its assets for the benefit of its educational and research
# purposes, GRL makes clear that no condition is made or to be implied, nor is any warranty given or to be implied, as to
# the accuracy of the Software, or that it will be suitable for any particular purpose or for use under any specific
# conditions. Furthermore, GRL disclaims all responsibility for the use which is made of the Software. It further
# disclaims any liability for the outcomes arising from using  the Software.
# 
# The Licensee agrees to indemnify GRL and hold GRL harmless from and against any and all claims, damages and liabilities
# asserted by third parties (including claims for negligence) which arise directly or indirectly from the use of the
# Software or the sale of any products based on the Software.
# 
# No part of the Software may be reproduced, modified, transmitted or transferred in any form or by any means, electronic
# or mechanical, without the express permission of GRL. The permission of GRL is not required if the said reproduction,
# modification, transmission or transference is done without financial return, the conditions of this Licence are imposed
# upon the receiver of the product, and all original and amended source code is included in any transmitted product. You
# may be held legally responsible for any copyright infringement that is caused or encouraged by your failure to abide by
# these terms and conditions.
# 
# You are not permitted under this Licence to use this Software commercially. Use for which any financial return is
# received shall be defined as commercial use, and includes (1) integration of all or part of the source code or the
# Software into a product for sale or license by or on behalf of Licensee to third parties or (2) use of the Software
# or any derivative of it for research with the final aim of developing software products for sale or license to a third
# party or (3) use of the Software or any derivative of it for research with the final aim of developing non-software
# products for sale or license to a third party, or (4) use of the Software to provide any service to an external
# organisation for which payment is received. If you are interested in using the Software commercially, please contact
# legal@sanger.ac.uk. Contact details are: legal@sanger.ac.uk quoting reference Valiant-software.
#############################

import abc
from collections.abc import Sized
from typing import Callable, ClassVar, Dict, List, Set
import numpy as np
import pandas as pd
from .codon_table import CodonTable, STOP_CODE
from .mutated_sequences import (
    DeletionMutatedSequence,
    Deletion1MutatedSequence,
    Deletion2Offset0MutatedSequence,
    Deletion2Offset1MutatedSequence,
    MutationCollection,
    SingleNucleotideMutatedSequence,
    SingleCodonMutatedSequence
)
from .pam_protection import PamProtectedReferenceSequence
from .snv_table import AuxiliaryTables
from ..enums import TargetonMutator, VariantType
from ..string_mutators import delete_non_overlapping_3_offset, replace_codons_const
from ..utils import get_constant_category, get_out_of_frame_offset


def get_snv_mutations(sequence: str) -> MutationCollection:
    return MutationCollection.from_variants(
        SingleNucleotideMutatedSequence.from_sequence(
            sequence))


class BaseTargeton(abc.ABC, Sized):
    MUTATORS: ClassVar[Set[TargetonMutator]] = {
        TargetonMutator.SNV,
        TargetonMutator.DEL1,
        TargetonMutator.DEL2_0,
        TargetonMutator.DEL2_1
    }

    def __init__(self, ref_sequence: PamProtectedReferenceSequence) -> None:
        self.ref_sequence: PamProtectedReferenceSequence = ref_sequence

    def __len__(self) -> int:
        return len(self.sequence)

    @property
    def sequence(self) -> str:
        return self.ref_sequence.pam_protected_sequence

    def _get_mutator_method(self, mutator: TargetonMutator):
        return getattr(self, f"get_{mutator.value.replace('-', '_')}_mutations")

    def get_mutations(self, mutator: TargetonMutator, aux_tables: AuxiliaryTables = None) -> MutationCollection:
        if mutator not in self.MUTATORS:
            raise ValueError(f"Invalid mutator '{mutator.value}' for targeton!")

        return self._get_mutator_method(mutator)(aux_tables=aux_tables)

    def get_1del_mutations(self, **kwargs) -> MutationCollection:
        return MutationCollection.from_variants(
            Deletion1MutatedSequence.from_sequence(self.sequence))

    def get_2del0_mutations(self, **kwargs) -> MutationCollection:
        return MutationCollection.from_variants(
            Deletion2Offset0MutatedSequence.from_sequence(self.sequence))

    def get_2del1_mutations(self, **kwargs) -> MutationCollection:
        return MutationCollection.from_variants(
            Deletion2Offset1MutatedSequence.from_sequence(self.sequence))

    def get_snv_mutations(self, **kwargs) -> MutationCollection:
        return get_snv_mutations(self.sequence)

    def _compute_mutations(
        self,
        mutators: Set[TargetonMutator],
        aux_tables: AuxiliaryTables = None
    ) -> Dict[TargetonMutator, MutationCollection]:
        return {
            mutator: self.get_mutations(mutator, aux_tables=aux_tables)
            for mutator in mutators
        }


class Targeton(BaseTargeton):
    __slots__ = {'ref_sequence'}

    def compute_mutations(self, mutators: Set[TargetonMutator]) -> Dict[TargetonMutator, MutationCollection]:
        return super()._compute_mutations(mutators)


class CDSTargeton(BaseTargeton):
    __slots__ = {'ref_sequence', 'cds_prefix', 'cds_suffix'}

    MUTATORS: ClassVar[Set[TargetonMutator]] = {
        TargetonMutator.DEL1,
        TargetonMutator.DEL2_0,
        TargetonMutator.DEL2_1,
        TargetonMutator.IN_FRAME,
        TargetonMutator.SNV,
        TargetonMutator.SNV_RE,
        TargetonMutator.STOP,
        TargetonMutator.ALA,
        TargetonMutator.AA
    }

    SNVRE_MUTATORS: ClassVar[Set[TargetonMutator]] = {
        TargetonMutator.SNV_RE
    }

    def __init__(self, sequence: PamProtectedReferenceSequence, cds_prefix: str, cds_suffix: str) -> None:
        super().__init__(sequence)
        self.cds_prefix: str = cds_prefix
        self.cds_suffix: str = cds_suffix

    def __post_init__(self) -> None:
        if (len(self) + len(self.cds_prefix) + len(self.cds_suffix)) % 3 != 0:
            raise ValueError("Invalid length for in-frame sequence!")

    @property
    def strand(self) -> str:
        return self.ref_sequence.genomic_range.strand

    @property
    def cds_sequence(self) -> str:
        return f"{self.cds_prefix}{self.sequence}{self.cds_suffix}"

    @property
    def frame(self) -> int:
        return len(self.cds_prefix)

    @property
    def cds_prefix_length(self) -> int:
        return len(self.cds_prefix)

    @property
    def cds_suffix_length(self) -> int:
        return len(self.cds_suffix)

    @property
    def start(self) -> int:
        return self.ref_sequence.genomic_range.start

    @property
    def cds_sequence_start(self) -> int:
        return self.ref_sequence.genomic_range.start - self.frame

    def _add_snv_metadata(
        self,
        aux: AuxiliaryTables,
        snv_meta_full: pd.DataFrame,
        snvs: MutationCollection
    ) -> MutationCollection:

        if snvs.df is None:
            return snvs

        # Make SNV data comparable with pre-computed metadata
        snv_meta = snv_meta_full[[
            'pos',
            'alt',
            'ref_aa',
            'alt_aa',
            'mut_type'
        ]].rename(columns={
            'pos': 'mut_position',
            'alt': 'new',
            'ref_aa': 'ref_aa',
            'alt_aa': 'alt_aa',
            'mut_type': 'mut_type'
        }).set_index(['mut_position', 'new'])
        snvs.df.mut_position += self.start
        df = snvs.df.set_index(['mut_position', 'new'], drop=False)

        # Join SNV data with pre-computed metadata
        snv_joint = df.join(snv_meta)
        snv_joint = snv_joint.reset_index(drop=True)

        # TODO: to remove once the later step do not update the position
        snv_joint.mut_position -= self.start

        # Wrap complete SNV metadata in a collection
        return MutationCollection(
            df=snv_joint, mutations=snvs.mutations)

    def _get_snvres(self, aux: AuxiliaryTables, snvs: pd.DataFrame) -> MutationCollection:
        df: pd.DataFrame = aux.snvre_table.get_snvres(
            self.ref_sequence.genomic_range, self.frame, self.sequence, snvs).rename(
                columns={
                    'pos': 'mut_position',
                    'alt': 'new',
                    'ref_aa': 'ref_aa',
                    'alt_aa': 'alt_aa',
                    'mut_type': 'mut_type'
                })

        # TODO: avoid generating mutation list when possible
        return MutationCollection(df=df, mutations=[
            SingleCodonMutatedSequence(r.mut_position, r.mseq, r.ref, r.new)
            for r in df.itertuples()
        ])

    def _get_codon_mutations(self, codon_table: CodonTable, aa: str) -> MutationCollection:

        # Retrieve top codon for amino acid (or stop)
        get_top_ranking_codon: Callable[[str], str] = (
            codon_table.get_top_ranking_codon if self.strand == '+' else
            codon_table.get_top_ranking_codon_rc
        )
        codon: str = get_top_ranking_codon(aa)

        # Generate single-codon substitutions
        offset: int = get_out_of_frame_offset(self.frame)
        mc: MutationCollection = MutationCollection.from_variants([
            SingleCodonMutatedSequence(pos, mseq, ref, alt)
            for pos, ref, alt, mseq in replace_codons_const(self.sequence, offset, codon)
        ])

        if mc.df is None:
            raise RuntimeError("Mutation collection table not found!")

        # Get amino acid information
        tr: Callable[[str], str] = (
            codon_table.translate if self.strand == '+' else
            codon_table.translate_rc
        )
        rown: int = mc.df.shape[0]
        amino_acid_symbols: List[str] = codon_table.amino_acid_symbols
        mc.df['ref_aa'] = pd.Categorical(mc.df.ref.apply(tr), categories=amino_acid_symbols)
        mc.df['alt_aa'] = get_constant_category(aa, rown, amino_acid_symbols)

        # Add variant type
        mc.df['var_type'] = np.int8(VariantType.SUBSTITUTION.value)

        return mc

    def get_ala_mutations(self, aux_tables: AuxiliaryTables = None) -> MutationCollection:
        if not aux_tables:
            raise RuntimeError("Codon table not provided!")
        codon_table: CodonTable = aux_tables.codon_table
        return self._get_codon_mutations(codon_table, 'A')

    def get_stop_mutations(self, aux_tables: AuxiliaryTables = None) -> MutationCollection:
        if not aux_tables:
            raise RuntimeError("Codon table not provided!")
        codon_table: CodonTable = aux_tables.codon_table
        return self._get_codon_mutations(codon_table, STOP_CODE)

    def get_aa_mutations(self, aux_tables: AuxiliaryTables = None) -> MutationCollection:
        if not aux_tables:
            raise RuntimeError("Auxiliary tables not provided!")
        df: pd.DataFrame = aux_tables.all_aa_table.get_subs(
            self.ref_sequence.genomic_range, self.frame, self.sequence)
        return MutationCollection(df=df, mutations=[
            SingleCodonMutatedSequence(r.mut_position, r.mseq, r.ref, r.new)
            for r in df.itertuples()
        ])

    def compute_mutations(self, mutators: Set[TargetonMutator], aux: AuxiliaryTables) -> Dict[TargetonMutator, MutationCollection]:

        # Classify mutators
        base_mutators = mutators - self.SNVRE_MUTATORS
        snvre_mutators = mutators & self.SNVRE_MUTATORS

        if snvre_mutators:
            base_mutators.add(TargetonMutator.SNV)

        # Compute base mutations (overwrites existing)
        mutations: Dict[TargetonMutator, MutationCollection] = super()._compute_mutations(
            base_mutators, aux_tables=aux)

        if TargetonMutator.SNV in base_mutators:

            # Retrieve pre-computed metadata
            snv_meta_full = aux.snv_table.get_snvs(
                self.strand,
                self.cds_sequence,
                self.ref_sequence.genomic_range,
                self.cds_prefix_length,
                self.cds_suffix_length,
                reset_index=False)

            # Attach pre-computed metadata to SNV's
            snvs: MutationCollection = self._add_snv_metadata(aux, snv_meta_full, mutations[TargetonMutator.SNV])
            mutations[TargetonMutator.SNV] = snvs

            # TODO: refactor dispatch
            for mutator in snvre_mutators:
                if mutator == TargetonMutator.SNV_RE:

                    # Compute SNVRE mutations
                    mutations[TargetonMutator.SNV_RE] = self._get_snvres(aux, snv_meta_full)

                else:
                    raise NotImplementedError(f"Mutator '{mutator.value}' not yet implemented!")

        return mutations

    def get_inframe_mutations(self, **kwargs) -> MutationCollection:
        start_offset: int = get_out_of_frame_offset(self.cds_prefix_length)
        end_offset: int = get_out_of_frame_offset(self.cds_suffix_length)
        return MutationCollection.from_variants([
            DeletionMutatedSequence(pos, mseq, ref_seq)
            for pos, ref_seq, mseq in delete_non_overlapping_3_offset(
                self.sequence, start_offset, end_offset)
        ])
