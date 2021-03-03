pragma solidity ^0.5.0;
pragma experimental ABIEncoderV2;

interface PoolInfo {
     struct Tuple1 { uint256 A; uint256 future_A; uint256 fee; uint256 admin_fee; uint256 future_fee; uint256 future_admin_fee; address future_owner; uint256 initial_A; uint256 initial_A_time; uint256 future_A_time; }

     function address_provider () external view returns (address);
     function get_pool_coins (address _pool) external view returns (address[8] memory coins, address[8] memory underlying_coins, uint256[8] memory decimals, uint256[8] memory underlying_decimals);
     function get_pool_info (address _pool) external view returns (uint256[8] memory balances, uint256[8] memory underlying_balances, uint256[8] memory decimals, uint256[8] memory underlying_decimals, uint256[8] memory rates, address lp_token, Tuple1 memory params);
}