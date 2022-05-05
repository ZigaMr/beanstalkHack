# beanstalkHack
Python + Hardhat PoC of BeanStalk Hack April 2022

Smart contract code is forked from https://github.com/abdulsamijay/Beanstalk-Exploit-POC all credits to @abdulsamijay.
Hardhat + web3.py doesn't allow for address spoofing, so I had to recreate the hack from the start (Bean tokens approve/desposit...).

Steps to run:


1: Start hardhat node
  npx hardhat node

2: Run python file 
  src/test/test_beanstalk_hack.py 

Make sure to update the needed parameters (path + rpc archive node) in test_beanstalk_hack.py and hardhat.config files
