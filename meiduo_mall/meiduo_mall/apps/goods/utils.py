from collections import OrderedDict

from goods.models import GoodsChannel


def get_categories():
    """
    获取商城商品分类菜单
    :return 菜单字典
    """
    # 商品频道及分类菜单
    # 使用有序字典保存类别的顺序
    # categories = {
    #     1: { # 组1
    #         'channels': [{'id':xxx, 'name':xxx, 'url':xxx},{}, {}...],
    #         'subunits': [{'id':xxx, 'name':xxx, 'subunits':[{},{}]}]
    #     },
    #     2: { # 组2
    #          ......
    #     }
    # }

    # 有序字典
    categories = OrderedDict()
    # 先按照频道id排序，在按照组内顺序排序
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        # 获取当前组
        group_id = channel.group_id
        if group_id not in categories:
            categories[group_id] = {'channels': {}, 'subunits': []}

        # 当前频道类别
        cat1 = channel.category

        # 追加当前频道
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # 构建当前类别的子类别
        for cat2 in cat1.goodscategory_set.all():
            cat2.subunits = []
            for cat3 in cat2.goodscategory_set.all():
                cat2.subunits.append(cat3)
            categories[group_id]['subunits'].append(cat2)

    return categories