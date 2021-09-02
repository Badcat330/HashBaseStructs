from __future__ import annotations
import hashlib
import json
from math import sqrt, ceil
from typing import Any, NoReturn, Union, Callable, Optional, List
from blake3 import blake3
from tigerhash import tigerhash

__all__ = ['MerkleHashGrid']


class MerkleNode(object):
    def __init__(self, hsh: Union[bytes, bytearray]) -> None:
        self.hsh = hsh


class GridNode(MerkleNode):
    def __init__(self, key: Any, value: Any, hsh: Union[bytes, bytearray]) -> None:
        super().__init__(hsh)
        self.key = key
        self.value = value


class MerkleNodePlaceInfo(object):
    def __init__(self, tree: List[List[MerkleNode]], level_index: int = 0, item_index: int = 0) -> NoReturn:
        self.tree = tree
        self.level_index = level_index
        self.item_index = item_index

    def get_node(self) -> Optional[MerkleNode]:
        if self.level_index >= len(self.tree) or self.item_index >= len(self.tree[self.level_index]):
            return None

        return self.tree[self.level_index][self.item_index]

    def is_last(self) -> bool:
        return self.level_index == len(self.tree) - 1

    def size(self) -> int:
        return len(self.tree[-1])

    def left_children(self) -> MerkleNodePlaceInfo:
        return MerkleNodePlaceInfo(self.tree, self.level_index + 1, self.item_index * 2)

    def right_children(self) -> MerkleNodePlaceInfo:
        return MerkleNodePlaceInfo(self.tree, self.level_index + 1, self.item_index * 2 + 1)


class MerkleHashGrid(object):

    def __init__(self, hsh: Union[str, Callable[[Union[bytes, bytearray]],
                                                Union[bytes, bytearray]]] = 'sha256') -> None:
        if isinstance(hsh, str):
            try:
                if hsh == 'blake3':
                    self.hash_function = blake3
                elif hsh == 'tigerhash':
                    self.hash_function = tigerhash
                else:
                    self.hash_function = getattr(hashlib, hsh)
            except AttributeError:
                raise Exception(f'{hsh} is not supported')
        elif callable(hsh):
            self._get_hash = hsh
        else:
            raise Exception("Incorrect hash argument")

        self.nodes = []
        self.row_tree = []
        self.column_tree = []
        self.grid_side = 0
        self.grid_size = 0
        self.master_hash = b''

    def _get_hash(self, value: Union[bytes, bytearray]) -> Union[bytes, bytearray]:
        value = str(value)
        value = value.encode('utf-8')
        hash_value = self.hash_function(value).digest()
        return hash_value

    def clear(self) -> NoReturn:
        self.nodes = []
        self.row_tree = []
        self.column_tree = []
        self.grid_side = 0
        self.grid_size = 0
        self.master_hash = bytearray()

    def add_iter(self, keys, values) -> NoReturn:
        indexes = []
        for key, value in zip(keys, values):
            indexes.append(self._setitem(key, value, is_build=False))

        self._build(indexes)

    def add_dict(self, dct: dict):
        indexes = []
        for key in dct:
            indexes.append(self._setitem(key, value=dct[key], is_build=False))

        self._build(indexes)

    @property
    def size(self) -> int:
        return self.grid_size

    @property
    def root_hash(self) -> bytes:
        return self.master_hash

    def get_changeset(self, destination: MerkleHashGrid) -> List[dict]:
        if self.master_hash == destination.master_hash:
            return []

        row_indexes = MerkleHashGrid._find_inconsistencies(MerkleNodePlaceInfo(self.row_tree),
                                                           MerkleNodePlaceInfo(destination.row_tree))
        column_indexes = MerkleHashGrid._find_inconsistencies(MerkleNodePlaceInfo(self.column_tree),
                                                              MerkleNodePlaceInfo(destination.column_tree))
        source_dict = {}
        destination_dict = {}
        answer = []

        for row in row_indexes:
            for column in column_indexes:
                index = row * self.grid_side + column
                destination_node = None
                source_node = None

                if index >= len(self.nodes):
                    destination_node = destination.nodes[index]
                if index >= len(destination.nodes):
                    source_node = self.nodes[index]

                if destination_node is not None and \
                        source_node is not None and \
                        destination_node.key == source_node.key:
                    answer += self._format_change(source=source_node,
                                                  destination=destination_node)
                else:
                    if destination_node is not None:
                        if destination_node.key in source_dict:
                            answer += self._format_change(source=source_dict.pop(destination_node.key),
                                                          destination=destination_node)
                        else:
                            destination_dict[destination_node.key] = destination_node
                    if source_node is not None:
                        if source_node.key in destination_dict:
                            answer += self._format_change(source=source_node,
                                                          destination=destination_dict.pop(source_node.key))
                        else:
                            source_dict[source_node.key] = source_node

        for key in source_dict:
            answer += self._format_change(source=source_dict[key])

        for key in destination_dict:
            answer += self._format_change(destination=destination_dict[key])

        return answer

    @staticmethod
    def _format_change(source: Optional[GridNode] = None, destination: Optional[GridNode] = None) -> List[dict]:
        if source is None:
            return [{
                'Operation type': 'Create',
                'Key': destination.key,
                'Value': destination.value
            }]
        elif destination is None:
            return [{
                'Operation type': 'Delete',
                'Key': source.key,
                'Value': source.value
            }]
        elif source.hsh != destination.hsh:
            return [{
                'Operation type': 'Update',
                'Key': source.key,
                'Source value': source.value,
                'Destination value': destination.value
            }]
        else:
            return []

    @staticmethod
    def _find_inconsistencies(source_info: MerkleNodePlaceInfo, destination_info: MerkleNodePlaceInfo) -> List[int]:
        source_node = source_info.get_node()
        destination_node = destination_info.get_node()

        if source_node is None or destination_node is None or source_node.hsh == destination_node.hsh:
            return []

        if source_info.is_last() and destination_info.is_last():
            if source_info.size() > destination_info.size():
                return [source_info.item_index]
            else:
                return [destination_info.item_index]
        elif source_info.is_last():
            left_children = destination_info.left_children()
            right_children = destination_info.right_children()
            return MerkleHashGrid._find_inconsistencies(source_info, left_children) + \
                   MerkleHashGrid._find_inconsistencies(source_info, right_children)
        elif destination_info.is_last():
            left_children = source_info.left_children()
            right_children = source_info.right_children()
            return MerkleHashGrid._find_inconsistencies(left_children, destination_info) + \
                   MerkleHashGrid._find_inconsistencies(right_children, destination_info)
        else:
            left_children_destination = destination_info.left_children()
            right_children_destination = destination_info.right_children()
            left_children_source = source_info.left_children()
            right_children_source = source_info.right_children()
            return MerkleHashGrid._find_inconsistencies(left_children_source, left_children_destination) + \
                   MerkleHashGrid._find_inconsistencies(right_children_source, right_children_destination)

    def swap(self, other_tree: MerkleHashGrid) -> NoReturn:
        self.hash_function, other_tree.hash_function = other_tree.hash_function, self.hash_function
        self.nodes, other_tree.nodes = other_tree.nodes, self.nodes
        self.row_tree, other_tree.row_tree = other_tree.row_tree, self.row_tree
        self.column_tree, other_tree.column_tree = other_tree.column_tree, self.column_tree
        self.grid_side, other_tree.grid_side = other_tree.grid_side, self.grid_side
        self.grid_size, other_tree.grid_size = other_tree.grid_size, self.grid_size
        self.master_hash, other_tree.master_hash = other_tree.master_hash, self.master_hash

    def _find_position(self, key: Any) -> int:
        min_index = 0
        max_index = len(self.nodes) - 1
        mid_index = (max_index + min_index) // 2

        while max_index >= min_index:
            if self.nodes[mid_index].key == key:
                return mid_index
            elif self.nodes[mid_index].key < key:
                min_index = mid_index + 1
            else:
                max_index = mid_index - 1
            mid_index = (max_index + min_index) // 2

        if mid_index == -1:
            return 0

        return mid_index

    def get(self, key: Any, verified: bool = False) -> Any:
        index = self._find_position(key)

        if verified:
            # TODO Add verified
            pass

        if self.nodes[index].key == key:
            return self.nodes[index].value
        else:
            raise Exception("No such element")

    def __getitem__(self, key: Any) -> Any:
        return self.get(key)

    def delete(self, key: Any) -> NoReturn:
        index = self._find_position(key)

        if self.nodes[index].key == key:
            self.nodes.pop(index)
            self.nodes -= 1
            self._build([index])
        else:
            raise Exception("No such element")

    def __delitem__(self, key: Any) -> NoReturn:
        self.delete(key)

    def _setitem(self, key, value: object, is_build: bool) -> Optional[int]:
        index = self._find_position(key)

        if index >= len(self.nodes) or self.nodes[index].key > key:
            self.nodes.insert(index, GridNode(key, value, self._get_hash(value)))
            self.grid_size += 1
        elif key == self.nodes[index].key:
            self.nodes[index].value = value
        else:
            self.nodes.insert(index + 1, GridNode(key, value, self._get_hash(value)))
            self.grid_size += 1

        if is_build:
            self._build([index])
        else:
            return index

    def _build(self, indexes: Union[List[int]]):
        new_grid_side = ceil(sqrt(self.grid_size))
        if new_grid_side != self.grid_side:
            self.grid_side = new_grid_side
            self._build_column_tree()
            self._build_row_tree()
        elif all(new_grid_side ** 2 - new_grid_side >= index for index in indexes):
            self._build_row_tree(new_grid_side ** 2 - new_grid_side)
            self._build_column_tree(list(map(lambda x: x % new_grid_side, indexes)))
        else:
            self._build_column_tree()
            min_index = min(indexes)
            start_index = min_index - min_index % new_grid_side
            self._build_row_tree(list(range(start_index, self.grid_size, new_grid_side)))

        self.master_hash = self._get_hash(self.row_tree[0][0] + self.column_tree[0][0])

    def _build_row_tree(self, index: Optional[List[int]] = None):
        if index is None:
            index = range(0, self.grid_size, self.grid_side)

        first_row_level = []

        for i in index:
            row_sum = b""
            for j in range(0, self.grid_side):
                if i + j >= len(self.nodes):
                    break
                row_sum += self.nodes[i + j].hsh
            first_row_level.append(MerkleNode(self._get_hash(row_sum)))

        self.row_tree.append(first_row_level)

        while len(self.row_tree[0]) > 1:
            self.row_tree = [self._calculate_next_level(self.row_tree[0]), ] + self.row_tree

    def _build_column_tree(self, index: Optional[List[int]] = None):
        if index is None:
            index = range(0, self.grid_side)

        first_column_level = []

        for i in index:
            column_sum = b""
            for j in range(0, self.grid_size, self.grid_side):
                if i + j >= len(self.nodes):
                    break
                column_sum += self.nodes[i + j].hsh
            first_column_level.append(MerkleNode(self._get_hash(column_sum)))

        self.column_tree.append(first_column_level)

        while len(self.column_tree) > 1:
            self.column_tree = [self._calculate_next_level(self.column_tree[0]), ] + self.column_tree

    def _calculate_next_level(self, prev_level: list[MerkleNode]) -> list[MerkleNode]:
        new_level = []

        for i in range(1, len(prev_level), 2):
            left = prev_level[i - 1]
            right = prev_level[i]
            new_element = MerkleNode(self._get_hash(left.hsh + right.hsh))
            new_level.append(new_element)

        if len(prev_level) % 2 == 1:
            last_element = prev_level[-1]
            new_level.append(MerkleNode(last_element.hsh))

        return new_level

    def set(self, key: Any, value: Any) -> NoReturn:
        self._setitem(key, value, is_build=True)

    def __setitem__(self, key: Any, value: Any) -> NoReturn:
        self._setitem(key, value, is_build=True)

    def get_by_order(self, order: int, as_json: bool = False):
        data = {'key': self.nodes[order].key, 'value': self.nodes[order].value}

        if not as_json:
            return data
        else:
            return json.dumps(data)

    def __iter__(self, as_json: bool = False) -> iter:
        for node in self.nodes:
            data = {'key': node.key, 'value': node.value}
            if not as_json:
                yield data
            else:
                yield json.dumps(data)

    def __contains__(self, key: Any) -> bool:
        index = self._find_position(key)

        if index < len(self.nodes) and self.nodes[index].key == key:
            return True
        else:
            return False

    def __len__(self):
        return self.size

    def __eq__(self, o: object) -> bool:
        if type(o) is MerkleHashGrid:
            return self.root_hash == o.root_hash
        else:
            return False

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __str__(self) -> str:
        # TODO: finish str
        pass

    def verify(self, vo: tuple, hsh="sha256"):
        # TODO:
        pass
