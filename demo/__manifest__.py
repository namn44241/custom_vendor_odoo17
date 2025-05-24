{
    'name': 'Demo - Quản lý công ty, kho và hàng lỗi',
    'version': '1.0',
    'summary': 'Triển khai các tính năng quản lý công ty, kho và hàng lỗi',
    'description': """
        Module này triển khai các tính năng:
        - Kiểm soát công ty con mua hàng từ nhà cung cấp ngoài
        - Quản lý hàng lỗi với 3 loại: hàng bỏ, hàng sửa chữa, hàng trả
        - Tự động chọn kho gần nhất dựa trên GPS
    """,
    'category': 'Inventory/Inventory',
    'author': '',
    'website': '',
    'depends': ['base', 'purchase', 'stock', 'sale_management', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/res_partner_views.xml',
        'views/stock_scrap_views.xml',
        'views/sale_order_views.xml',
        'views/stock_menu.xml',
        'views/warehouse_finder_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}