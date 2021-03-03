pragma solidity ^0.5.0;

interface CurveCalc {
     function get_dx (uint256 n_coins, uint256[8] calldata balances, uint256 amp, uint256 fee, uint256[8] calldata rates, uint256[8] calldata precisions, int128 i, int128 j, uint256 dy) external view returns (uint256);
     function get_dy (uint256 n_coins, uint256[8] calldata balances, uint256 amp, uint256 fee, uint256[8] calldata rates, uint256[8] calldata precisions, int128 i, int128 j, uint256[100] calldata dx) external view returns (uint256[100] memory);
}