class CCliError(Exception): pass

class CCliClientError(CCliError): pass
class CCliClientConnectionError(CCliClientError): pass
class CCliClientKeyspaceError(CCliClientError): pass
