from sqlalchemy.ext.asyncio import create_async_engine

import config


engine = create_async_engine(url=config.DB_URI, echo=False)
