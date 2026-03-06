# coding:utf-8
from typing import List

from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlRecord

from ..entity import Entity, EntityFactory
from .sql_query import SqlQuery


def finishQuery(func):
    """ Finish sql query to unlock database """

    def wrapper(dao, *args, **kwargs):
        result = func(dao, *args, **kwargs)
        dao.query.finish()
        return result

    return wrapper


class DaoBase:
    """ Database access operation abstract class """

    table = ''
    fields = ['id']

    def __init__(self, db: QSqlDatabase = None):
        self.setDatabase(db)

    def createTable(self):
        """ create table """
        raise NotImplementedError

    @finishQuery
    def selectBy(self, **condition) -> Entity:
        """ query a record that meet the conditions

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entity: Entity
            entity instance, `None` if no record is found
        """
        self._prepareSelectBy(condition)

        if not (self.query.exec() and self.query.first()):
            return None

        return self.loadFromRecord(self.query.record())

    def selectByPage(self, pageNum=1, pageSize=10, **condition):
        """ query records that meet the conditions from specified page

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entity: Entity
            entity instance, `None` if no record is found
        """
        condition['limit'] = ((pageNum - 1) * pageSize, pageSize)
        return self.listBy(**condition)

    def selectLikePage(self, pageNum=1, pageSize=10, **condition):
        """ Fuzzy query records that meet the conditions from specified page

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entity: Entity
            entity instance, `None` if no record is found
        """
        condition['limit'] = ((pageNum - 1) * pageSize, pageSize)
        return self.listLike(**condition)

    def listBy(self, **condition) -> List[Entity]:
        """ query all records that meet the conditions

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entities: List[Entity]
            entity instances, empty if no records are found
        """
        self._prepareSelectBy(condition)

        if not self.query.exec():
            return []

        return self.iterRecords()

    def listLike(self, **condition) -> List[Entity]:
        """ Fuzzy query all records that meet the conditions (or relationships)

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entities: List[Entity]
            entity instances, empty if no records are found
        """
        self._prepareSelectLike(condition)

        if not self.query.exec():
            return []

        return self.iterRecords()

    def listBySql(self, sql: str):
        if not self.query.exec(sql):
            return []

        return self.iterRecords()

    def _prepareSelectBy(self, condition: dict):
        """ prepare sql select statement

        Parameters
        ----------
        table: str
            table name

        condition: dict
            query condition
        """
        if not condition:
            raise ValueError("At least one condition must be passed in")

        commands = ['orderBy', 'limit', 'desc', 'asc']
        sql = f"SELECT * FROM {self.table}"

        keys = [i for i in condition.keys() if i not in commands]
        if keys:
            where = [f'{k} = ?' for k in keys]
            sql += f" WHERE  {' AND '.join(where)}"

        sql = self._addConditionToSql(sql, condition)

        self.query.prepare(sql)
        for k in keys:
            self.query.addBindValue(condition[k])

    def _prepareSelectLike(self, condition: dict):
        """ prepare sql fuzzy select statement

        Parameters
        ----------
        table: str
            table name

        condition: dict
            query condition
        """
        if not condition:
            raise ValueError("At least one condition must be passed in")

        sql = f"SELECT * FROM {self.table}"

        commands = ['orderBy', 'limit', 'desc', 'asc']
        likeKeys = [k for k in condition.keys() if k not in commands]

        if likeKeys:
            placeholders = [f"{k} like ?" for k in likeKeys]
            sql += f" WHERE {' OR '.join(placeholders)}"

        sql = self._addConditionToSql(sql, condition)

        self.query.prepare(sql)
        for k in likeKeys:
            self.query.addBindValue(f'%{condition[k]}%')

    def _addConditionToSql(self, sql: str, condition: dict):
        if 'orderBy' in condition:
            sql += f" ORDER BY {condition['orderBy']}"
            if 'desc' in condition and condition['desc']:
                sql += ' DESC'
            elif 'asc' in condition and condition['asc']:
                sql += ' ASC'

        if 'limit' in condition:
            limit = condition['limit']
            if isinstance(limit, int):
                sql += f" LIMIT {limit}"
            elif isinstance(limit, tuple):
                sql += f" LIMIT {limit[0]},{limit[1]}"

        return sql

    def listAll(self) -> List[Entity]:
        """ query all records """
        sql = f"SELECT * FROM {self.table}"
        if not self.query.exec(sql):
            return []

        return self.iterRecords()

    def listByFields(self, field: str, values: list):
        """ query the records of field values in the list """
        if field not in self.fields:
            raise ValueError(f"field name `{field}` is illegal")

        if not values:
            return []

        placeHolders = ','.join(['?']*len(values))
        sql = f"SELECT * FROM {self.table} WHERE {field} IN ({placeHolders})"
        self.query.prepare(sql)

        for value in values:
            self.query.addBindValue(value)

        if not self.query.exec():
            return []

        return self.iterRecords()

    def listByIds(self, ids: list) -> List[Entity]:
        """ query the records of the primary key value in the list """
        return self.listByFields(self.fields[0], ids)

    @finishQuery
    def iterRecords(self) -> List[Entity]:
        """ iterate over all queried records """
        entities = []

        while self.query.next():
            entity = self.loadFromRecord(self.query.record())
            entities.append(entity)

        return entities

    @finishQuery
    def update(self, id, field: str, value) -> bool:
        """ update the value of a field in a record

        Parameters
        ----------
        id:
            primary key value

        filed: str
            field name

        value:
            field value

        Returns
        -------
        success: bool
            is the update successful
        """
        sql = f"UPDATE {self.table} SET {field} = ? WHERE {self.fields[0]} = ?"
        self.query.prepare(sql)
        self.query.addBindValue(value)
        self.query.addBindValue(id)
        return self.query.exec()

    @finishQuery
    def updateByField(self, field: str, old, new) -> bool:
        """ update the value of a field in a record

        Parameters
        ----------
        filed: str
            field name

        old:
            old field value

        new:
            new filed value

        Returns
        -------
        success: bool
            is the update successful
        """
        sql = f"UPDATE {self.table} SET {field} = ? WHERE {field} = ?"
        self.query.prepare(sql)
        self.query.addBindValue(new)
        self.query.addBindValue(old)
        return self.query.exec()

    @finishQuery
    def updateById(self, entity: Entity) -> bool:
        """ update a record

        Parameters
        ----------
        entity: Entity
            entity instance

        Returns
        -------
        success: bool
            is the update successful
        """
        if len(self.fields) <= 1:
            return False

        id_ = self.fields[0]
        values = ','.join([f'{i} = :{i}' for i in self.fields[1:]])
        sql = f"UPDATE {self.table} SET {values} WHERE {id_} = :{id_}"

        self.query.prepare(sql)
        self.bindEntityToQuery(entity)

        return self.query.exec()

    @finishQuery
    def updateByIds(self, entities: List[Entity]) -> bool:
        """ update multi records

        Parameters
        ----------
        entities: List[Entity]
            entity instances

        Returns
        -------
        success: bool
            is the update successful
        """
        if not entities:
            return True

        if len(self.fields) <= 1:
            return False

        db = self.getDatabase()
        db.transaction()

        id_ = self.fields[0]
        values = ','.join([f'{i} = :{i}' for i in self.fields[1:]])
        sql = f"UPDATE {self.table} SET {values} WHERE {id_} = :{id_}"

        self.query.prepare(sql)

        for entity in entities:
            self.bindEntityToQuery(entity)
            self.query.exec()

        success = db.commit()
        return success

    @finishQuery
    def insert(self, entity: Entity) -> bool:
        """ insert a record

        Parameters
        ----------
        entity: Entity
            entity instance

        Returns
        -------
        success: bool
            is the insert successful
        """
        values = ','.join([f':{i}' for i in self.fields])
        sql = f"INSERT INTO {self.table} VALUES ({values})"
        self.query.prepare(sql)
        self.bindEntityToQuery(entity)
        return self.query.exec()

    @finishQuery
    def insertBatch(self, entities: List[Entity], ignore=False) -> bool:
        """ insert multi records

        Parameters
        ----------
        entities: List[Entity]
            entity instances

        ignore: bool
            If the primary key exists, the corresponding row will not be inserted when `ignore=True`

        Returns
        -------
        success: bool
            is the insert successful
        """
        if not entities:
            return True

        db = self.getDatabase()
        db.transaction()

        values = ','.join([f':{i}' for i in self.fields])
        if not ignore:
            sql = f"INSERT INTO {self.table} VALUES ({values})"
        else:
            sql = f"INSERT OR IGNORE INTO {self.table} VALUES ({values})"

        self.query.prepare(sql)

        for entity in entities:
            self.bindEntityToQuery(entity)
            self.query.exec()

        return db.commit()

    @finishQuery
    def insertOrUpdate(self, entity: Entity):
        """ insert a new record or update the record if it already exists

        Parameters
        ----------
        entity: Entity
            entity instance

        Returns
        -------
        success: bool
            is the insert successful
        """
        # insert a new record or ignore it if the primary key already exists
        values = ','.join([f':{i}' for i in self.fields])
        sql = f"INSERT OR IGNORE INTO {self.table} VALUES ({values})"
        self.query.prepare(sql)
        self.bindEntityToQuery(entity)
        success = self.query.exec()

        # update record
        success &= self.updateById(entity)
        return success

    @finishQuery
    def deleteById(self, id) -> bool:
        """ delete a record

        Parameters
        ----------
        id:
            primary key value

        Returns
        -------
        success: bool
            is the delete successful
        """
        sql = f"DELETE FROM {self.table} WHERE {self.fields[0]} = ?"
        self.query.prepare(sql)
        self.query.addBindValue(id)
        return self.query.exec()

    @finishQuery
    def deleteByFields(self, field: str, values: list):
        """ delete multi records based on the value of a field """
        if field not in self.fields:
            raise ValueError(f"field name `{field}` is illegal")

        if not values:
            return True

        placeHolders = ','.join(['?']*len(values))
        sql = f"DELETE FROM {self.table} WHERE {field} IN ({placeHolders})"
        self.query.prepare(sql)

        for value in values:
            self.query.addBindValue(value)

        return self.query.exec()

    @finishQuery
    def deleteByMultiFields(self, **condition):
        """ delete multi records based on the value of multi fields """
        if not condition:
            return

        placeHolders = []
        keys = list(condition.keys())
        for _ in range(len(condition[keys[0]])):
            placeHolder = ' AND '.join([f"{k} = ?" for k in keys])
            placeHolders.append(f"({placeHolder})")

        sql = f"DELETE FROM {self.table} WHERE {' OR '.join(placeHolders)}"
        self.query.prepare(sql)

        for value in zip(*condition.values()):
            for v in value:
                self.query.addBindValue(v)

        return self.query.exec()

    def deleteByIds(self, ids: list) -> bool:
        """ delete multi records

        Parameters
        ----------
        ids: list
            primary key values

        Returns
        -------
        success: bool
            is the delete successful
        """
        return self.deleteByFields(self.fields[0], ids)

    def count(self):
        """ Returns the count of rows """
        success = self.query.exec(f"SELECT COUNT(*) from {self.table}")
        if not success:
            return 0

        return self.query.record().value(0) if self.query.next() else 0

    def clearTable(self):
        """ clear all data from table """
        return self.query.exec(f"DELETE FROM {self.table}")

    @classmethod
    def loadFromRecord(cls, record: QSqlRecord) -> Entity:
        """ create an entity instance from a record

        Parameters
        ----------
        record: QSqlRecord
            record

        Returns
        -------
        entity: Entity
            entity instance
        """
        entity = EntityFactory.create(cls.table)

        for i in range(record.count()):
            field = record.fieldName(i)

            if isinstance(entity[field], QDateTime):
                entity[field] = QDateTime.fromString(record.value(i), Qt.DateFormat.ISODateWithMs)
            elif isinstance(entity[field], bool):
                entity[field] = bool(record.value(i))
            else:
                entity[field] = record.value(i)

        return entity

    def adjustText(self, text: str):
        """ handling single quotation marks in strings """
        return text.replace("'", "''")

    def bindEntityToQuery(self, entity: Entity):
        """ bind the value of entity to query object """
        for field in self.fields:
            value = entity[field]
            self.query.bindValue(f':{field}', value)

    def setDatabase(self, db: QSqlDatabase):
        """ use the specified database """
        self.connectionName = db.connectionName() if db else ''
        self.query = SqlQuery(db) if db else SqlQuery()
        self.query.setForwardOnly(True)

    def getDatabase(self):
        """ get connected database """
        if self.connectionName:
            return QSqlDatabase.database(self.connectionName)

        return QSqlDatabase.database()
