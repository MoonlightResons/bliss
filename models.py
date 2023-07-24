from peewee import *
import datetime
from flask_login import UserMixin
from playhouse.migrate import PostgresqlMigrator, migrate

db = PostgresqlDatabase(
    'galaxy1',
    host = 'localhost',
    port = '5432',
    user = 'lada_sedan',
    password = 'qwe123'
)

db.connect()

class BaseModel(Model):
    class Meta:
        database = db
        
        
class MyUser(UserMixin, BaseModel):
    username = CharField(max_length=255, null=False, unique=True)
    email = CharField(max_length=255, null=False, unique=True)
    age = IntegerField()
    full_name = CharField(max_length=255, null=True)
    password = CharField(max_length=255, null=False)
    avatar_filename = CharField(max_length=255, null=True)

    def __repr__(self):
        return self.email

    
    
class Post(BaseModel):
    author = ForeignKeyField(MyUser, on_delete='CASCADE')
    title = CharField(max_length=255, null=False)
    content = TextField()
    created_date = DateTimeField(default=datetime.datetime.now)
    cover_filename = CharField(max_length=255, null=True)

    def get_likes_count(self):
        return Like.select().where(Like.post == self).count()

    
class Like(BaseModel):
    user = ForeignKeyField(MyUser, backref='likes')
    post = ForeignKeyField(Post, backref='likes')

    class Meta:
        indexes = ((('user', 'post'), True),)

db.create_tables([MyUser, Post,Like])


# migrator = PostgresqlMigrator(db)
# migrate(
#     migrator.add_column('post', 'avatar_filename', CharField(max_length=255, null=True))
# )
