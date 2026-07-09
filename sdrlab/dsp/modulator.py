"""
Modulator interface and plugin-based implementations.
Provides extensible class hierarchy for BPSK, QPSK, and future QAM modules.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Type


class BaseModulator(ABC):
    """
    Abstract Base Class for all modulation formats.
    Defines interface for digital mapping and demapping of bits and symbols.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the modulation format."""
        pass

    @property
    @abstractmethod
    def bits_per_symbol(self) -> int:
        """Number of bits mapped into a single modulation symbol."""
        pass

    @property
    @abstractmethod
    def constellation(self) -> np.ndarray:
        """Array of all valid constellation points in complex space."""
        pass

    @abstractmethod
    def map_bits_to_symbols(self, bits: np.ndarray) -> np.ndarray:
        """
        Maps a 1D array of binary bits into a 1D array of complex symbols.
        
        Args:
            bits: 1D array of 0s and 1s.
            
        Returns:
            np.ndarray: Complex-valued mapped symbols.
        """
        pass

    @abstractmethod
    def demap_symbols_to_bits(self, symbols: np.ndarray) -> np.ndarray:
        """
        Demaps complex symbols to binary bits using maximum likelihood detection (minimum Euclidean distance).
        
        Args:
            symbols: 1D array of received complex symbols.
            
        Returns:
            np.ndarray: 1D array of reconstructed binary bits.
        """
        pass


class BPSKModulator(BaseModulator):
    """
    Binary Phase Shift Keying (BPSK) Modulator.
    Maps 1 bit to 1 symbol (+1 or -1).
    """

    @property
    def name(self) -> str:
        return "BPSK"

    @property
    def bits_per_symbol(self) -> int:
        return 1

    @property
    def constellation(self) -> np.ndarray:
        return np.array([1.0 + 0.0j, -1.0 + 0.0j], dtype=complex)

    def map_bits_to_symbols(self, bits: np.ndarray) -> np.ndarray:
        # Validate bits format
        if not np.all((bits == 0) | (bits == 1)):
            raise ValueError("Input bits must be strictly 0 or 1.")
        
        # 0 -> +1.0, 1 -> -1.0
        return 1.0 - 2.0 * bits.astype(float) + 0.0j

    def demap_symbols_to_bits(self, symbols: np.ndarray) -> np.ndarray:
        # Hard decision threshold at 0 on real axis
        # symbol real > 0 -> bit 0, symbol real <= 0 -> bit 1
        return (symbols.real < 0.0).astype(int)


class QPSKModulator(BaseModulator):
    """
    Quadrature Phase Shift Keying (QPSK) Modulator with Gray coding.
    Maps 2 bits to 1 symbol.
    """

    @property
    def name(self) -> str:
        return "QPSK"

    @property
    def bits_per_symbol(self) -> int:
        return 2

    @property
    def constellation(self) -> np.ndarray:
        c = np.array([1+1j, -1+1j, 1-1j, -1-1j]) / np.sqrt(2.0)
        return c.astype(complex)

    def map_bits_to_symbols(self, bits: np.ndarray) -> np.ndarray:
        if len(bits) % 2 != 0:
            raise ValueError("QPSK modulation requires an even number of bits.")
        if not np.all((bits == 0) | (bits == 1)):
            raise ValueError("Input bits must be strictly 0 or 1.")
        
        # Reshape to group bits in pairs
        reshaped_bits = bits.reshape(-1, 2)
        b0 = reshaped_bits[:, 0]
        b1 = reshaped_bits[:, 1]
        
        # Gray-coded QPSK mapping:
        # 00 -> 1/sqrt(2) + j/sqrt(2)
        # 01 -> 1/sqrt(2) - j/sqrt(2)
        # 10 -> -1/sqrt(2) + j/sqrt(2)
        # 11 -> -1/sqrt(2) - j/sqrt(2)
        d_I = 1.0 - 2.0 * b0
        d_Q = 1.0 - 2.0 * b1
        
        symbols = (d_I + 1j * d_Q) / np.sqrt(2.0)
        return symbols

    def demap_symbols_to_bits(self, symbols: np.ndarray) -> np.ndarray:
        # Gray-coded QPSK demapping:
        # Real axis determines first bit (positive -> 0, negative -> 1)
        # Imag axis determines second bit (positive -> 0, negative -> 1)
        num_symbols = len(symbols)
        bits = np.zeros((num_symbols, 2), dtype=int)
        
        bits[:, 0] = (symbols.real < 0.0).astype(int)
        bits[:, 1] = (symbols.imag < 0.0).astype(int)
        
        return bits.flatten()


class ModulatorFactory:
    """
    Registry and Factory class for Modulators.
    Enables new modulators to register and be loaded dynamically by string name.
    """

    _registry: Dict[str, Type[BaseModulator]] = {
        "BPSK": BPSKModulator,
        "QPSK": QPSKModulator,
    }

    @classmethod
    def register(cls, name: str, modulator_class: Type[BaseModulator]) -> None:
        """Registers a new modulator class to the plugin system."""
        cls._registry[name.upper()] = modulator_class

    @classmethod
    def get_modulator(cls, name: str) -> BaseModulator:
        """Retrieves and instantiates a modulator by its format name."""
        name_upper = name.upper()
        if name_upper not in cls._registry:
            raise KeyError(
                f"Modulation format '{name}' is not registered. Registered formats: {list(cls._registry.keys())}"
            )
        return cls._registry[name_upper]()
