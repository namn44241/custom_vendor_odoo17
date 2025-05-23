from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_subsidiary = fields.Boolean(string='Là công ty con', default=False)
    is_parent_company = fields.Boolean(string='Là công ty mẹ', default=False)
    is_external_vendor = fields.Boolean(string='Là nhà cung cấp ngoài', default=False)
    
    # Thêm các trường tọa độ GPS
    latitude = fields.Float(string='Vĩ độ', digits=(16, 8), readonly=True)
    longitude = fields.Float(string='Kinh độ', digits=(16, 8), readonly=True)
    
    @api.onchange('is_subsidiary', 'is_parent_company', 'is_external_vendor')
    def _onchange_company_type(self):
        if self.is_subsidiary:
            self.is_parent_company = False
            self.is_external_vendor = False
        elif self.is_parent_company:
            self.is_subsidiary = False
            self.is_external_vendor = False
        elif self.is_external_vendor:
            self.is_subsidiary = False
            self.is_parent_company = False

    def action_fetch_geolocation(self):
        """Gọi API Nominatim để lấy lat/long theo địa chỉ hiện tại."""
        self.ensure_one()
        # Kiểm tra đủ thông tin địa chỉ để query
        if not (self.street or self.city or self.state_id or self.country_id):
            raise UserError(_("Vui lòng nhập tối thiểu Street, City, State, Country"))
        # Gom thành chuỗi địa chỉ
        parts = filter(None, [
            self.street,
            self.street2,
            self.city,
            self.state_id.name if self.state_id else None,
            self.country_id.name if self.country_id else None,
        ])
        query = ", ".join(parts)
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
        }
        headers = {'User-Agent': 'Odoo-Geocoder/1.0'}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise UserError(_("Không thể gọi tới dịch vụ địa lý: %s") % e)
        if not data:
            raise UserError(_("Không tìm thấy tọa độ cho địa chỉ: %s") % query)
        # Gán kết quả
        self.latitude = float(data[0].get('lat', 0.0))
        self.longitude = float(data[0].get('lon', 0.0))
        # Thông báo thành công
        self.message_post(body=_("Lấy tọa độ thành công: %s, %s") % (self.latitude, self.longitude)) 