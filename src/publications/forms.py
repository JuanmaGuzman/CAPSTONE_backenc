from django.forms import ModelForm, IntegerField
from publications.models import Publication, Item, Category


class ItemCreationForm(ModelForm):
    category_id = IntegerField()

    class Meta:
        model = Item
        fields = ('name', 'brand', 'size', 'color', 'sku')

    def clean_cateogry_id(self):
        category_id = self.cleaned_data['category_id']
        category_query = Category.objects.filter(id=category_id)
        if not category_query.exists():
            self.add_error(
                'category_id',
                'Category not found.'
            )
        return category_id

    def clean(self):
        super().clean()
        self.clean_cateogry_id()

    def save(self, commit=True):
        item = super(ItemCreationForm, self).save(commit=False)
        # lower case baby
        item.name = item.name.lower()
        item.brand = item.brand.lower()
        item.color = item.color.lower()
        item.size = item.size.lower()
        item.category = Category.objects.get(
            pk=self.cleaned_data['category_id']
        )
        if commit:
            item.save()
        return item


class PublicationCreationForm(ModelForm):
    class Meta:
        model = Publication
        fields = ('price', 'description')


class CategoryCreationForm(ModelForm):
    class Meta:
        model = Category
        fields = ('name',)

    def save(self, commit=True):
        cat = super(CategoryCreationForm, self).save(commit=False)
        cat.name = cat.name.lower()
        if commit:
            cat.save()
        return cat
