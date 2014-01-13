

class StockReportValidationError(Exception):
    """
    Error that a stock report didn't validate properly
    """
    pass


class TooMuchStockError(StockReportValidationError):
    """
    When someone reports too much stock.
    """
    def __init__(self, product, amount, max, *args, **kwargs):
        super(TooMuchStockError, self).__init__(self, *args, **kwargs)
        self.product = product
        self.amount = amount
        self.max = max

    def __str__(self):
        return '{amount} is too much {product}. max allowed is {max}.'.format(
            amount=self.amount,
            product=self.product,
            max=self.max,
        )