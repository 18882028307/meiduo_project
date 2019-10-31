import xadmin
from xadmin import views

from . import models
from orders import models as omodels


class BaseSetting(object):
    """xadmin的基本配置"""
    enable_themes = True    # 开启主题切换功能
    use_bootswatch = True


xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSettings(object):
    """xadmin的全局配置"""
    site_title = "眉度商城运营管理系统"   # 设置站点标题
    site_footer = '眉度商城集团有限公司'  # 设置站点页脚
    menu_style = 'accordion'    # 设置菜单折叠


xadmin.site.register(views.CommAdminView, GlobalSettings)


class SKUSpecificationAdmin(object):
    def save_models(self):
        obj = self.new_obj
        obj.seve()

        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

    def delete_model(self):
        obj = self.obj
        sku_id = obj.sku.id
        obj.delete()

        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)


class SKUAdmin(object):
    model_icon = 'fa fa-gift'
    list_display = ['id', 'name', 'price', 'stock', 'sales', 'comments']


class OrderAdmin(object):
    # 列表显示的字段
    list_display = ['order_id', 'create_time', 'total_amount', 'pay_method', 'status']
    # 支持按多长时间(秒)刷新页面
    refresh_times = [3, 5]
    data_charts = {
    "order_amount": {'title': '订单金额', "x-field": "create_time", "y-field": ('total_amount',), "order": ('create_time',)}, "order_count": {'title': '订单量', "x-field": "create_time", "y-field": ('total_count',), "order": ('create_time',)},
    }

xadmin.site.register(models.GoodsCategory)
xadmin.site.register(models.GoodsChannel)
xadmin.site.register(models.Goods)
xadmin.site.register(models.Brand)
xadmin.site.register(models.GoodsSpecification)
xadmin.site.register(models.SpecificationOption)
xadmin.site.register(models.SKU, SKUAdmin)
xadmin.site.register(models.SKUImage)
xadmin.site.register(models.SKUSpecification, SKUSpecificationAdmin)

xadmin.site.register(omodels.OrderInfo, OrderAdmin)