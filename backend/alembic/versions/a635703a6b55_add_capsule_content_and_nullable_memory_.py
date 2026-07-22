from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'a635703a6b55'
down_revision: Union[str, None] = 'ef300e1cd3c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """SQLite 不支持 ALTER COLUMN 和命名外键约束，需重建表来实现：
    1. memory_id 改为可空
    2. 外键 ondelete 从 CASCADE 改为 SET NULL
    3. 添加 content 列
    注意：content 列可能已存在（部分迁移），需检查
    """
    conn = op.get_bind()

    # 检查 content 列是否已存在
    result = conn.execute(text("PRAGMA table_info(time_capsules)"))
    columns = [row[1] for row in result]
    content_exists = 'content' in columns

    if not content_exists:
        op.add_column('time_capsules', sa.Column('content', sa.TEXT(), nullable=True))

    # 使用 batch_alter_table 重建表：memory_id 改为可空
    # SQLite batch 模式会自动重建表，但无法通过名称删除匿名外键约束
    # 因此使用原始 SQL 方式重建表来同时修改外键行为
    # 先备份
    op.execute(text(
        "CREATE TABLE _time_capsules_backup AS SELECT * FROM time_capsules"
    ))
    # 删除原表
    op.execute(text("DROP TABLE time_capsules"))
    # 创建新表（memory_id 可空 + FK SET NULL + content 列）
    op.execute(text("""
        CREATE TABLE time_capsules (
            id VARCHAR(36) NOT NULL,
            memory_id VARCHAR(36),
            title VARCHAR(500) NOT NULL,
            open_date DATETIME NOT NULL,
            buried_date DATETIME NOT NULL,
            status VARCHAR(11) NOT NULL,
            opened_at DATETIME,
            is_forced BOOLEAN NOT NULL,
            message TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            content TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(memory_id) REFERENCES memories (id) ON DELETE SET NULL
        )
    """))
    # 复制数据
    op.execute(text(
        "INSERT INTO time_capsules SELECT * FROM _time_capsules_backup"
    ))
    # 删除备份
    op.execute(text("DROP TABLE _time_capsules_backup"))


def downgrade() -> None:
    """回滚：memory_id 改回 NOT NULL，外键改回 CASCADE，删除 content 列"""
    conn = op.get_bind()

    # 备份
    op.execute(text(
        "CREATE TABLE _time_capsules_backup AS SELECT * FROM time_capsules"
    ))
    # 删除原表
    op.execute(text("DROP TABLE time_capsules"))
    # 创建旧结构表
    op.execute(text("""
        CREATE TABLE time_capsules (
            id VARCHAR(36) NOT NULL,
            memory_id VARCHAR(36) NOT NULL,
            title VARCHAR(500) NOT NULL,
            open_date DATETIME NOT NULL,
            buried_date DATETIME NOT NULL,
            status VARCHAR(11) NOT NULL,
            opened_at DATETIME,
            is_forced BOOLEAN NOT NULL,
            message TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(memory_id) REFERENCES memories (id) ON DELETE CASCADE
        )
    """))
    # 复制数据（排除 content 列）
    op.execute(text(
        "INSERT INTO time_capsules (id, memory_id, title, open_date, buried_date, status, opened_at, is_forced, message, created_at, updated_at) "
        "SELECT id, memory_id, title, open_date, buried_date, status, opened_at, is_forced, message, created_at, updated_at "
        "FROM _time_capsules_backup"
    ))
    # 删除备份
    op.execute(text("DROP TABLE _time_capsules_backup"))