from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Kho hàng') 

    @api.constrains('product_uom_qty')
    def _check_positive_quantity(self):
        for line in self:
            if line.product_id.type == 'product' and line.product_uom_qty <= 0:
                raise ValidationError(_(
                    "Số lượng cho sản phẩm '%s' phải lớn hơn 0."
                ) % line.product_id.display_name) 