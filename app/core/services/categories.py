from ..exceptions import ValidationError
from ... import models
from ...models.utils import lock_by_user


class CategoryManager:
    user: models.User

    def __init__(self, *, user: models.User) -> None:
        self.user = user

    async def create_category(self, *, name: str) -> models.Category:
        async with lock_by_user(self.user.id):
            has_category_with_the_same_name = await models.Category.filter(
                name=name,
                owner=self.user,
            ).exists()

            if has_category_with_the_same_name:
                raise ValidationError('You already have a category with this name')

            return await models.Category.create(
                name=name,
                owner=self.user,
            )

    async def get_categories(self) -> tuple[models.Category, ...]:
        return tuple(await models.Category.filter(
            owner=self.user,
        ).order_by(
            'name',
        ))

    async def get_category(self, category_id: int) -> models.Category:
        category = await models.Category.get(
            id=category_id,
            owner=self.user,
        )
        category.owner = self.user  # To prevent the query
        return category

    async def get_category_by_name(self, category_name: str) -> models.Category:
        category = await models.Category.get(
            name=category_name,
            owner=self.user,
        )
        category.owner = self.user  # To prevent the query
        return category

    @staticmethod
    async def update_category_name(*, category: models.Category, new_name: str) -> None:
        category.name = new_name
        await category.save(update_fields=('name',))

    async def delete_category(self, *, category_id: int) -> None:
        async with lock_by_user(self.user.id):
            await models.Category.filter(
                id=category_id,
                owner=self.user,
            ).delete()
