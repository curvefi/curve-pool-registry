# @version 0.2.15


interface Initializable:
    def initialize(): nonpayable


gauge_implementation: public(address)


@external
def __init__(_gauge_impl: address):
    self.gauge_implementation = _gauge_impl


@external
def deploy():
    proxy: address = create_forwarder_to(self.gauge_implementation)
    Initializable(proxy).initialize()
