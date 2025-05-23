from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class WarehouseFinderWizard(models.TransientModel):
    _name = 'warehouse.finder.wizard'
    _description = 'Tìm kho phù hợp nhất có đủ hàng'
    
    sale_order_id = fields.Many2one('sale.order', string='Đơn hàng')
    found_warehouse_id = fields.Many2one('stock.warehouse', string='Kho được tìm thấy')
    message = fields.Text(string='Thông báo')
    has_warehouse = fields.Boolean(string='Có kho phù hợp', default=False)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order = self.env['sale.order'].browse(self.env.context.get('active_id') or False)
        if order:
            wh, ok = order._find_nearest_warehouse_with_stock()
            res.update({
                'sale_order_id': order.id,
                'found_warehouse_id': wh.id if ok else False,
                'has_warehouse': ok,
                'message': ok and _(
                    "Tìm được kho gần nhất: %s (State: %s)"
                ) % (
                    wh.name,
                    (wh.partner_id.state_id.name or 'N/A')
                ) or _("Không tìm được kho nào phù hợp. Kho gần nhất không có hàng hoặc không có tọa độ GPS."),
            })
        return res
    
    def action_confirm(self):
        """Áp dụng kho đã tìm thấy vào đơn hàng"""
        self.ensure_one()
        if self.found_warehouse_id and self.sale_order_id:
            # Cập nhật warehouse_id của đơn hàng
            self.sale_order_id.warehouse_id = self.found_warehouse_id.id
            # Cập nhật warehouse_id cho từng dòng
            for line in self.sale_order_id.order_line.filtered(lambda l: l.product_id.type=='product'):
                line.warehouse_id = self.found_warehouse_id.id
            # Thông báo thành công
            self.sale_order_id.message_post(body=_("Đã chọn kho gần nhất: %s") % self.found_warehouse_id.name)
        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        """Đóng wizard mà không thực hiện hành động"""
        return {'type': 'ir.actions.act_window_close'} 