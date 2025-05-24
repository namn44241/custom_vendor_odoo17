from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    @api.constrains('partner_id', 'company_id')
    def _check_external_vendor_for_subsidiary(self):
        for order in self:
            company_partner = order.company_id.partner_id
            if company_partner.is_subsidiary and order.partner_id.is_external_vendor:
                raise ValidationError(_('Công ty con không được phép mua hàng từ nhà cung cấp ngoài!'))
    
    @api.onchange('partner_id')
    def _onchange_partner_warning(self):
        if not self.partner_id:
            return
        current_company = self.env.company
        if current_company.partner_id.is_subsidiary and self.partner_id.is_external_vendor:
            return {
                'warning': {
                    'title': _("Cảnh báo!"),
                    'message': _("Công ty con không được phép mua hàng từ nhà cung cấp ngoài.\n"
                                "Vui lòng chọn nhà cung cấp khác hoặc mua hàng thông qua công ty mẹ."),
                }
            } 