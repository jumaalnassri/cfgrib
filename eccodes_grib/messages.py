#
# Copyright 2017-2018 B-Open Solutions srl.
# Copyright 2017-2018 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import bytes

import collections
import typing as T  # noqa

import attr

from . import eccodes


@attr.attrs()
class Message(collections.Mapping):
    codes_id = attr.attrib()
    path = attr.attrib(default=None)
    offset = attr.attrib(default=None)
    key_encoding = attr.attrib(default='ascii')
    value_encoding = attr.attrib(default='ascii')

    def __del__(self):
        try:
            eccodes.codes_handle_delete(self.codes_id)
        except:
            pass

    def message_get(self, item, key_type=None, strict=True):
        # type: (bytes, int, bool) -> T.Any
        """Get value of a given key as its native or specified type."""
        ret = None
        size = eccodes.codes_get_size(self.codes_id, item)
        if size > 1:
            ret = eccodes.codes_get_array(self.codes_id, item, key_type=key_type)
        elif size == 1:
            ret = eccodes.codes_get(self.codes_id, item, key_type=key_type, strict=strict)
        return ret

    def message_iterkeys(self, namespace=None):
        # type: (bytes) -> T.Generator[bytes, None, None]
        iterator = eccodes.codes_keys_iterator_new(self.codes_id, namespace=namespace)
        while eccodes.codes_keys_iterator_next(iterator):
            yield eccodes.codes_keys_iterator_get_name(iterator)
        eccodes.codes_keys_iterator_delete(iterator)

    def __getitem__(self, item):
        # type: (str) -> T.Any
        key = item.encode(self.key_encoding)
        value = self.message_get(key)
        if isinstance(value, bytes):
            return value.decode(self.value_encoding)
        elif isinstance(value, list) and value and isinstance(value[0], bytes):
            return [v.decode(self.value_encoding) for v in value]
        else:
            return value

    def __iter__(self):
        # type: () -> T.Generator[str, None, None]
        for key in self.message_iterkeys():
            yield key.decode(self.key_encoding)

    def __len__(self):
        # type: () -> int
        return sum(1 for _ in self)


@attr.attrs()
class Stream(collections.Iterable):
    path = attr.attrib()
    mode = attr.attrib(default='r')

    def __iter__(self):
        # type: () -> T.Generator[Message, None, None]
        with open(self.path, self.mode) as file:
            while True:
                offset = file.tell()
                codes_id = eccodes.codes_new_from_file(file, eccodes.CODES_PRODUCT_GRIB)
                if not codes_id:
                    break
                yield Message(codes_id=codes_id, path=self.path, offset=offset)

    def first(self):
        return next(iter(self))