# @version 0.2.7


struct AddressInfo:
    addr: address
    is_active: bool
    version: uint256
    set_time: uint256
    description: String[64]


event NewAddressIdentifier:
    id: uint256
    addr: address
    description: String[64]

event AddressModified:
    id: uint256
    new_address: address
    version: uint256


event CommitNewAdmin:
    deadline: indexed(uint256)
    admin: indexed(address)

event NewAdmin:
    admin: indexed(address)


next_id: uint256
get_id_info: public(HashMap[uint256, AddressInfo])

admin: public(address)
transfer_ownership_deadline: public(uint256)
future_admin: public(address)


@external
def __init__():
    self.admin = msg.sender


@external
def max_id() -> uint256:
    return self.next_id - 1


@external
def get_address(_id: uint256) -> address:
    return self.get_id_info[_id].addr


@external
def add_new_id(_address: address, _description: String[64]) -> bool:
    assert msg.sender == self.admin

    id: uint256 = self.next_id
    self.get_id_info[id] = AddressInfo({
        addr: _address,
        is_active: True,
        version: 1,
        set_time: block.timestamp,
        description: _description
    })
    self.next_id = id + 1

    log NewAddressIdentifier(id, _address, _description)

    return True


@external
def set_address(_id: uint256, _address: address) -> bool:
    assert msg.sender == self.admin
    assert _address.is_contract

    version: uint256 = self.get_id_info[_id].version + 1
    assert version > 1

    self.get_id_info[_id].addr = _address
    self.get_id_info[_id].is_active = True
    self.get_id_info[_id].version = version
    self.get_id_info[_id].set_time = block.timestamp

    log AddressModified(_id, _address, version)

    return True


@external
def unset_address(_id: uint256) -> bool:
    assert msg.sender == self.admin

    version: uint256 = self.get_id_info[_id].version
    assert version != 0

    self.get_id_info[_id].is_active = False
    self.get_id_info[_id].addr = ZERO_ADDRESS
    self.get_id_info[_id].set_time = block.timestamp

    log AddressModified(_id, ZERO_ADDRESS, version)

    return True


@external
def commit_transfer_ownership(_new_admin: address) -> bool:
    """
    @notice Initiate a transfer of contract ownership
    @dev Once initiated, the actual transfer may be performed three days later
    @param _new_admin Address of the new owner account
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.transfer_ownership_deadline == 0  # dev: transfer already active

    deadline: uint256 = block.timestamp + 3*86400
    self.transfer_ownership_deadline = deadline
    self.future_admin = _new_admin

    log CommitNewAdmin(deadline, _new_admin)

    return True


@external
def apply_transfer_ownership() -> bool:
    """
    @notice Finalize a transfer of contract ownership
    @dev May only be called by the current owner, three days after a
         call to `commit_transfer_ownership`
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.transfer_ownership_deadline != 0  # dev: transfer not active
    assert block.timestamp >= self.transfer_ownership_deadline  # dev: now < deadline

    new_admin: address = self.future_admin
    self.admin = new_admin
    self.transfer_ownership_deadline = 0

    log NewAdmin(new_admin)

    return True


@external
def revert_transfer_ownership() -> bool:
    """
    @notice Revert a transfer of contract ownership
    @dev May only be called by the current owner
    """
    assert msg.sender == self.admin  # dev: admin-only function

    self.transfer_ownership_deadline = 0

    return True
