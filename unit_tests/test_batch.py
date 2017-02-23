# Copyright 2014 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest


class TestBatch(unittest.TestCase):

    @staticmethod
    def _get_target_class():
        from google.cloud.datastore.batch import Batch

        return Batch

    def _make_one(self, client):
        return self._get_target_class()(client)

    def test_ctor(self):
        from google.cloud.grpc.datastore.v1 import datastore_pb2

        _PROJECT = 'PROJECT'
        _NAMESPACE = 'NAMESPACE'
        connection = _Connection()
        client = _Client(_PROJECT, connection, _NAMESPACE)
        batch = self._make_one(client)

        self.assertEqual(batch.project, _PROJECT)
        self.assertIs(batch._client, client)
        self.assertEqual(batch.namespace, _NAMESPACE)
        self.assertIsNone(batch._id)
        self.assertEqual(batch._status, batch._INITIAL)
        self.assertIsInstance(batch._commit_request,
                              datastore_pb2.CommitRequest)
        self.assertIs(batch.mutations, batch._commit_request.mutations)
        self.assertEqual(batch._partial_key_entities, [])

    def test_current(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch1 = self._make_one(client)
        batch2 = self._make_one(client)
        self.assertIsNone(batch1.current())
        self.assertIsNone(batch2.current())
        with batch1:
            self.assertIs(batch1.current(), batch1)
            self.assertIs(batch2.current(), batch1)
            with batch2:
                self.assertIs(batch1.current(), batch2)
                self.assertIs(batch2.current(), batch2)
            self.assertIs(batch1.current(), batch1)
            self.assertIs(batch2.current(), batch1)
        self.assertIsNone(batch1.current())
        self.assertIsNone(batch2.current())

    def test_put_entity_wo_key(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)

        batch.begin()
        self.assertRaises(ValueError, batch.put, _Entity())

    def test_put_entity_wrong_status(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        entity = _Entity()
        entity.key = _Key('OTHER')

        self.assertEqual(batch._status, batch._INITIAL)
        self.assertRaises(ValueError, batch.put, entity)

    def test_put_entity_w_key_wrong_project(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        entity = _Entity()
        entity.key = _Key('OTHER')

        batch.begin()
        self.assertRaises(ValueError, batch.put, entity)

    def test_put_entity_w_partial_key(self):
        _PROJECT = 'PROJECT'
        _PROPERTIES = {'foo': 'bar'}
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        entity = _Entity(_PROPERTIES)
        key = entity.key = _Key(_PROJECT)
        key._id = None

        batch.begin()
        batch.put(entity)

        mutated_entity = _mutated_pb(self, batch.mutations, 'insert')
        self.assertEqual(mutated_entity.key, key._key)
        self.assertEqual(batch._partial_key_entities, [entity])

    def test_put_entity_w_completed_key(self):
        from google.cloud.datastore.helpers import _property_tuples

        _PROJECT = 'PROJECT'
        _PROPERTIES = {
            'foo': 'bar',
            'baz': 'qux',
            'spam': [1, 2, 3],
            'frotz': [],  # will be ignored
        }
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        entity = _Entity(_PROPERTIES)
        entity.exclude_from_indexes = ('baz', 'spam')
        key = entity.key = _Key(_PROJECT)

        batch.begin()
        batch.put(entity)

        mutated_entity = _mutated_pb(self, batch.mutations, 'upsert')
        self.assertEqual(mutated_entity.key, key._key)

        prop_dict = dict(_property_tuples(mutated_entity))
        self.assertEqual(len(prop_dict), 3)
        self.assertFalse(prop_dict['foo'].exclude_from_indexes)
        self.assertTrue(prop_dict['baz'].exclude_from_indexes)
        self.assertFalse(prop_dict['spam'].exclude_from_indexes)
        spam_values = prop_dict['spam'].array_value.values
        self.assertTrue(spam_values[0].exclude_from_indexes)
        self.assertTrue(spam_values[1].exclude_from_indexes)
        self.assertTrue(spam_values[2].exclude_from_indexes)
        self.assertFalse('frotz' in prop_dict)

    def test_delete_wrong_status(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        key = _Key(_PROJECT)
        key._id = None

        self.assertEqual(batch._status, batch._INITIAL)
        self.assertRaises(ValueError, batch.delete, key)

    def test_delete_w_partial_key(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        key = _Key(_PROJECT)
        key._id = None

        batch.begin()
        self.assertRaises(ValueError, batch.delete, key)

    def test_delete_w_key_wrong_project(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        key = _Key('OTHER')

        batch.begin()
        self.assertRaises(ValueError, batch.delete, key)

    def test_delete_w_completed_key(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)
        key = _Key(_PROJECT)

        batch.begin()
        batch.delete(key)

        mutated_key = _mutated_pb(self, batch.mutations, 'delete')
        self.assertEqual(mutated_key, key._key)

    def test_begin(self):
        _PROJECT = 'PROJECT'
        client = _Client(_PROJECT, None)
        batch = self._make_one(client)
        self.assertEqual(batch._status, batch._INITIAL)
        batch.begin()
        self.assertEqual(batch._status, batch._IN_PROGRESS)

    def test_begin_fail(self):
        _PROJECT = 'PROJECT'
        client = _Client(_PROJECT, None)
        batch = self._make_one(client)
        batch._status = batch._IN_PROGRESS
        with self.assertRaises(ValueError):
            batch.begin()

    def test_rollback(self):
        _PROJECT = 'PROJECT'
        client = _Client(_PROJECT, None)
        batch = self._make_one(client)
        batch.begin()
        self.assertEqual(batch._status, batch._IN_PROGRESS)
        batch.rollback()
        self.assertEqual(batch._status, batch._ABORTED)

    def test_rollback_wrong_status(self):
        _PROJECT = 'PROJECT'
        client = _Client(_PROJECT, None)
        batch = self._make_one(client)

        self.assertEqual(batch._status, batch._INITIAL)
        self.assertRaises(ValueError, batch.rollback)

    def test_commit(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)

        self.assertEqual(batch._status, batch._INITIAL)
        batch.begin()
        self.assertEqual(batch._status, batch._IN_PROGRESS)
        batch.commit()
        self.assertEqual(batch._status, batch._FINISHED)

        self.assertEqual(connection._committed,
                         [(_PROJECT, batch._commit_request, None)])

    def test_commit_wrong_status(self):
        _PROJECT = 'PROJECT'
        connection = _Connection()
        client = _Client(_PROJECT, connection)
        batch = self._make_one(client)

        self.assertEqual(batch._status, batch._INITIAL)
        self.assertRaises(ValueError, batch.commit)

    def test_commit_w_partial_key_entities(self):
        project = 'PROJECT'
        new_id = 1234
        connection = _Connection(new_id)
        client = _Client(project, connection)
        batch = self._make_one(client)
        entity = _Entity({})
        key = entity.key = _Key(project)
        key._id = None
        batch._partial_key_entities.append(entity)

        self.assertEqual(batch._status, batch._INITIAL)
        batch.begin()
        self.assertEqual(batch._status, batch._IN_PROGRESS)
        batch.commit()
        self.assertEqual(batch._status, batch._FINISHED)

        self.assertEqual(connection._committed,
                         [(project, batch._commit_request, None)])
        self.assertFalse(entity.key.is_partial)
        self.assertEqual(entity.key._id, new_id)

    def test_as_context_mgr_wo_error(self):
        _PROJECT = 'PROJECT'
        _PROPERTIES = {'foo': 'bar'}
        connection = _Connection()
        entity = _Entity(_PROPERTIES)
        key = entity.key = _Key(_PROJECT)

        client = _Client(_PROJECT, connection)
        self.assertEqual(list(client._batches), [])

        with self._make_one(client) as batch:
            self.assertEqual(list(client._batches), [batch])
            batch.put(entity)

        self.assertEqual(list(client._batches), [])

        mutated_entity = _mutated_pb(self, batch.mutations, 'upsert')
        self.assertEqual(mutated_entity.key, key._key)
        self.assertEqual(connection._committed,
                         [(_PROJECT, batch._commit_request, None)])

    def test_as_context_mgr_nested(self):
        _PROJECT = 'PROJECT'
        _PROPERTIES = {'foo': 'bar'}
        connection = _Connection()
        entity1 = _Entity(_PROPERTIES)
        key1 = entity1.key = _Key(_PROJECT)
        entity2 = _Entity(_PROPERTIES)
        key2 = entity2.key = _Key(_PROJECT)

        client = _Client(_PROJECT, connection)
        self.assertEqual(list(client._batches), [])

        with self._make_one(client) as batch1:
            self.assertEqual(list(client._batches), [batch1])
            batch1.put(entity1)
            with self._make_one(client) as batch2:
                self.assertEqual(list(client._batches), [batch2, batch1])
                batch2.put(entity2)

            self.assertEqual(list(client._batches), [batch1])

        self.assertEqual(list(client._batches), [])

        mutated_entity1 = _mutated_pb(self, batch1.mutations, 'upsert')
        self.assertEqual(mutated_entity1.key, key1._key)

        mutated_entity2 = _mutated_pb(self, batch2.mutations, 'upsert')
        self.assertEqual(mutated_entity2.key, key2._key)

        self.assertEqual(connection._committed,
                         [(_PROJECT, batch2._commit_request, None),
                          (_PROJECT, batch1._commit_request, None)])

    def test_as_context_mgr_w_error(self):
        _PROJECT = 'PROJECT'
        _PROPERTIES = {'foo': 'bar'}
        connection = _Connection()
        entity = _Entity(_PROPERTIES)
        key = entity.key = _Key(_PROJECT)

        client = _Client(_PROJECT, connection)
        self.assertEqual(list(client._batches), [])

        try:
            with self._make_one(client) as batch:
                self.assertEqual(list(client._batches), [batch])
                batch.put(entity)
                raise ValueError("testing")
        except ValueError:
            pass

        self.assertEqual(list(client._batches), [])

        mutated_entity = _mutated_pb(self, batch.mutations, 'upsert')
        self.assertEqual(mutated_entity.key, key._key)
        self.assertEqual(connection._committed, [])

    def test_as_context_mgr_enter_fails(self):
        klass = self._get_target_class()

        class FailedBegin(klass):

            def begin(self):
                raise RuntimeError

        client = _Client(None, None)
        self.assertEqual(client._batches, [])

        batch = FailedBegin(client)
        with self.assertRaises(RuntimeError):
            # The context manager will never be entered because
            # of the failure.
            with batch:  # pragma: NO COVER
                pass
        # Make sure no batch was added.
        self.assertEqual(client._batches, [])


class Test__parse_commit_response(unittest.TestCase):

    def _call_fut(self, commit_response_pb):
        from google.cloud.datastore.batch import _parse_commit_response

        return _parse_commit_response(commit_response_pb)

    def test_it(self):
        from google.cloud.grpc.datastore.v1 import datastore_pb2
        from google.cloud.grpc.datastore.v1 import entity_pb2

        index_updates = 1337
        keys = [
            entity_pb2.Key(
                path=[
                    entity_pb2.Key.PathElement(
                        kind='Foo',
                        id=1234,
                    ),
                ],
            ),
            entity_pb2.Key(
                path=[
                    entity_pb2.Key.PathElement(
                        kind='Bar',
                        name='baz',
                    ),
                ],
            ),
        ]
        response = datastore_pb2.CommitResponse(
            mutation_results=[
                datastore_pb2.MutationResult(key=key) for key in keys
            ],
            index_updates=index_updates,
        )
        result = self._call_fut(response)
        self.assertEqual(result, (index_updates, keys))


class _Connection(object):
    _marker = object()
    _save_result = (False, None)

    def __init__(self, *new_key_ids):
        from google.cloud.grpc.datastore.v1 import datastore_pb2

        self._committed = []
        mutation_results = [
            _make_mutation(key_id) for key_id in new_key_ids]
        self._commit_response_pb = datastore_pb2.CommitResponse(
            mutation_results=mutation_results)

    def commit(self, project, commit_request, transaction_id):
        self._committed.append((project, commit_request, transaction_id))
        return self._commit_response_pb


class _Entity(dict):
    key = None
    exclude_from_indexes = ()
    _meanings = {}


class _Key(object):
    _MARKER = object()
    _kind = 'KIND'
    _key = 'KEY'
    _path = None
    _id = 1234
    _stored = None

    def __init__(self, project):
        self.project = project

    @property
    def is_partial(self):
        return self._id is None

    def to_protobuf(self):
        from google.cloud.grpc.datastore.v1 import entity_pb2

        key = self._key = entity_pb2.Key()
        # Don't assign it, because it will just get ripped out
        # key.partition_id.project_id = self.project

        element = key.path.add()
        element.kind = self._kind
        if self._id is not None:
            element.id = self._id

        return key

    def completed_key(self, new_id):
        assert self.is_partial
        new_key = self.__class__(self.project)
        new_key._id = new_id
        return new_key


class _Client(object):

    def __init__(self, project, connection, namespace=None):
        self.project = project
        self._connection = connection
        self.namespace = namespace
        self._batches = []

    def _push_batch(self, batch):
        self._batches.insert(0, batch)

    def _pop_batch(self):
        return self._batches.pop(0)

    @property
    def current_batch(self):
        if self._batches:
            return self._batches[0]


def _assert_num_mutations(test_case, mutation_pb_list, num_mutations):
    test_case.assertEqual(len(mutation_pb_list), num_mutations)


def _mutated_pb(test_case, mutation_pb_list, mutation_type):
    # Make sure there is only one mutation.
    _assert_num_mutations(test_case, mutation_pb_list, 1)

    # We grab the only mutation.
    mutated_pb = mutation_pb_list[0]
    # Then check if it is the correct type.
    test_case.assertEqual(mutated_pb.WhichOneof('operation'),
                          mutation_type)

    return getattr(mutated_pb, mutation_type)


def _make_mutation(id_):
    from google.cloud.grpc.datastore.v1 import datastore_pb2
    from google.cloud.grpc.datastore.v1 import entity_pb2

    key = entity_pb2.Key()
    key.partition_id.project_id = 'PROJECT'
    elem = key.path.add()
    elem.kind = 'Kind'
    elem.id = id_
    return datastore_pb2.MutationResult(key=key)
