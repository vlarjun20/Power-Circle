pragma solidity ^0.8.0;

contract EnergyToken {
    string public name = "EnergyToken";
    string public symbol = "ETK";
    uint8 public decimals = 18;
    uint256 public totalSupply = 1000000 * (10 ** uint256(decimals));

    mapping(address => uint256) public balanceOf;

    constructor() {
        balanceOf[msg.sender] = totalSupply;
    }
}
