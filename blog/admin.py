from django.contrib import admin
from . import models

# categoryにカテゴリと一致してるものを表示
# さらにそこで編集できるように
class PostInline(admin.TabularInline):
    model = models.Post #post表示
    fields = ('title', 'body') #編集できるものを決める
    extra = 1 #空白のものを１ついれる

@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [PostInline]


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    pass

#自分でフィルターを作るときはadmin.SImpleLIstFilterを継承
class PostTitleFilter(admin.SimpleListFilter):
    title = '本文'
    parameter_name = 'body_contains'

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(body__icontains=self.value())
        return queryset

    def lookups(self, request, model_admin):
        return [
            ("ブログ", "「ブログ」を含む"),
            ("日記", "「日記」を含む"),
            ("開発", "「開発」を含む"),
        ]

#フォームを独自で作成する場合
from django import forms

# ちなみにこれはpost以外でも使える modelを指定してないから 
class PostAdminForm(forms.ModelForm):
    class Meta:
        labels = {
            'title': 'ブログタイトル',
        }
    # エラー表示をする
    def clean(self):
        body = self.cleaned_data.get('body') #ユーザの入力取得
        if '<' in body:
            raise forms.ValidationError('HTMLタグは使えません')


# post部分に表示するもの
@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm #上のformで作ったものを反映させる
    #個別関連のもの
    readonly_fields = ('created', 'updated')#編集しないフィールドはこっちにも書く
    # fields = ('title', 'body', 'category', 'tags', 'created', 'updated')
    fieldsets = [
        (None, {'fields': ('title', )}),
        ('コンテンツ', {'fields': ('body', )}),
        ('分類', {'fields': ('category', 'tags')}),
        ('メタ', {'fields': ('published', 'created', 'updated')})
    ]

# many to many field (タグ)の選び方変更
    filter_horizontal = ('tags',)

# 保存前、保存後に実行したい処理を書く　今回はprint
    def save_model(self, request, obj, form, change):
        print("before save")
        super().save_model(request, obj, form, change)
        print("after save")

# javascript読み込み
    class Media:
        js = ('post.js',)

    #リスト関連のもの
    list_display = ['id','title','category', 'tags_summary', 'published', 'created','updated']
    list_select_related = ('category',)    #Foreing key を呼ぶ時はこれつけると、実行時間が短くなる。
    list_editable = ('title', 'category') #編集できるようにする
    search_fields = ('title', 'category__name', 'tags__name', 'created', 'updated')
    #検索対象に何を入れるか指定する。postはいいけど、category,tagsはtags
    # の中のnameという部分までかく
    ordering = ("-updated",'-created') #並び順の指定 [-（ハイフン）]で逆順に
    list_filter = (PostTitleFilter,'category', 'tags', 'created', 'updated') #右のサイドバーを出してる
    actions = ["publish", "unpublish"]

    def tags_summary(self, obj):
        qs = obj.tags.all()
        label = ', '.join(map(str, qs))
        return label    

    tags_summary.short_description = "tags"

    # many to many keyも実行時間減らすためにこれをする
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('tags')   

    def publish(self, request, queryset):
        queryset.update(published=True)
        
    publish.short_description = "公開する"
        
    def unpublish(self, request, queryset):
        queryset.update(published=False)
        
    unpublish.short_description = "下書きに戻す"

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.admin import AdminSite

class BlogAdminSite(AdminSite):
    site_header = 'マイページ'
    site_title = 'マイページ'
    index_title = 'ホーム'
    site_url = None
    login_form = AuthenticationForm

    def has_permission(self, request):
        return request.user.is_active


mypage_site = BlogAdminSite(name="mypage") #インスタンス化

mypage_site.register(models.Post)
mypage_site.register(models.Tag)
mypage_site.register(models.Category)

# site_url = None 「サイトを表示」というのが無くなる
# ２６～２９スタッフじゃないユーザーも画面にログインするために必要
# 34～36で見せたい画面を登録