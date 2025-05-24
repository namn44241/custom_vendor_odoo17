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
    nearest_warehouse_id = fields.Many2one('stock.warehouse', string='Kho gần nhất')
    nearest_warehouse_distance = fields.Float(string='Khoảng cách (km)', digits=(10, 2))
    show_nearest_suggestion = fields.Boolean(string='Hiển thị gợi ý', default=False)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order = self.env['sale.order'].browse(self.env.context.get('active_id') or False)
        if order:
            wh, ok = order._find_nearest_warehouse_with_stock()
            
            # Tìm kho gần nhất ngay cả khi không có hàng
            partner = order.partner_shipping_id or order.partner_id
            nearest_wh = False
            min_distance = float('inf')
            
            if partner.latitude and partner.longitude:
                warehouses = self.env['stock.warehouse'].search([
                    ('company_id', '=', order.company_id.id)
                ])
                
                for warehouse in warehouses:
                    distance = warehouse.calculate_distance_to_partner(partner)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_wh = warehouse
            
            # Cập nhật thông tin
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
                'nearest_warehouse_id': nearest_wh.id if nearest_wh and not ok else False,
                'nearest_warehouse_distance': min_distance if min_distance < float('inf') else 0,
                'show_nearest_suggestion': bool(nearest_wh and not ok)
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
        """Đóng wizard và gọi hủy đơn hàng sale.order."""
        self.ensure_one()
        if self.sale_order_id:
            # Gọi phương thức hủy đơn của sale.order
            self.sale_order_id.action_cancel()
        # Đóng wizard
        return {'type': 'ir.actions.act_window_close'} 