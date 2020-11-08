.. _registry-address-provider:

================
Address Provider
================

``AddressProvider`` is an address provider for registry contracts.

Source code for this contract is available on `Github <https://github.com/curvefi/curve-pool-registry/blob/master/contracts/AddressProvider.vy>`_.

How it Works
============

The address provider is deployed to the Ethereum mainnet at:

    `0x0000000022D53366457F9d5E68Ec105046FC4383 <https://etherscan.io/address/0x0000000022d53366457f9d5e68ec105046fc4383>`_

This contract is immutable. The address will never change.

The address provider is the point-of-entry for on-chain integrators. All other contracts within the registry are assigned an ID within the address provider. IDs start from zero and increment as new components are added. The address associated with an ID may change, but the API of the associated contract will not.

Integrators requiring an aspect of the registry should always start by querying the address provider for the current address of the desired component. An up-to-date list of registered IDs is available :ref:`here <registry-address-provider-ids>`.

To interact with the address provider using the Brownie console:

.. code-block:: bash

    $ brownie console --network mainnet
    Brownie v1.11.10 - Python development framework for Ethereum

    Brownie environment is ready.
    >>> provider = Contract.from_explorer('0x0000000022D53366457F9d5E68Ec105046FC4383')
    Fetching source of 0x0000000022D53366457F9d5E68Ec105046FC4383 from api.etherscan.io...

    >>> provider
    <AddressProvider Contract '0x0000000022D53366457F9d5E68Ec105046FC4383'>

View Functions
==============

.. py:function:: AddressProvider.get_registry() -> address: view

    Get the address of the main registry contract.

    This is a more gas-efficient equivalent to calling :func:`get_address(0) <AddressProvider.get_address>`.

    .. code-block:: python

        >>> provider.get_registry()
        '0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c'

.. py:function:: AddressProvider.get_address(id: uint256) -> address: view

    Fetch the address associated with ``id``.

    .. code-block:: python

        >>> provider.get_address(1)
        '0xe64608E223433E8a03a1DaaeFD8Cb638C14B552C'

.. py:function:: AddressProvider.get_id_info(id: uint256) -> address, bool, uint256, uint256, string: view

    Fetch information about the given ``id``.

    Returns a tuple of the following:

    * ``address``: Address associated to the ID.
    * ``bool``: Is the address at this ID currently set?
    * ``uint256``: Version of the current ID. Each time the address is modified, this number increments.
    * ``uint256``: Epoch timestamp this ID was last modified.
    * ``string``: Human-readable description of the ID.

    .. code-block:: python

        >>> provider.get_id_info(1).dict()
        {
            'addr': "0xe64608E223433E8a03a1DaaeFD8Cb638C14B552C",
            'description': "PoolInfo Getters",
            'is_active': True,
            'last_modified': 1604019085,
            'version': 1
        }

.. py:function:: AddressProvider.max_id() -> uint256: view

    Get the highest ID set within the address provider.

    .. code-block:: python

        >>> provider.max_id()
        1

.. _registry-address-provider-ids:

Address IDs
===========

* ``0``: The main :ref:`registry contract<registry-registry>`. Used to locate pools and query information about them.
* ``1``: Aggregate getter methods for querying large data sets about a single pool. Designed for off-chain use.
* ``2``: Generalized swap contract. Used for finding rates and performing exchanges.
