import os
from collections import OrderedDict
from time import time

from django.conf import settings
from django.template import loader
from goods.models import GoodsChannel

from contents.models import ContentCategory



def generate_static_index_html():
    """
    生成静态的主页html
    :return:
    """
    print('%s: generate_static_index_html' % time().ctime())
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
    # 先按照频道id排序，再按照组内顺序排序
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        # 获取当前组
        group_id = channel.group_id

        if group_id not in categories:
            # 组建字典结构
            categories[group_id] = {'channels':[], 'subunits': []}

        cat1 = channel.category # 当前频道的类别

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

    # 广告内容
    contents = {}
    content_categories = ContentCategory.objects.all()

    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # 渲染模板
    context = {
        'categories': categories,
        'contents': contents
    }

    template = loader.get_template('index.html')
    html_text = template.render(context)

    # 将数据写到文件中，保存下来，形成静态文件
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')
    with open(file_path, 'w') as f:
        f.write(html_text)