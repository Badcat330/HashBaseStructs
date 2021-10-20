from __future__ import annotations
import hashlib
import json
from typing import Any, NoReturn, Optional, Union, Callable, List

__all__ = ['MerkleTree']


class MerkleTreeNode(object):
    def __init__(self, hsh: bytearray, size: int, max_key: Any, min_key: Any, avg: Any,
                 max_left_child: Any) -> NoReturn:
        self.hash = hsh
        self.size = size
        self.max_key = max_key
        self.min_key = min_key
        self.max_left_child = max_left_child
        self.avg = avg


class MerkleTreeLeaf(object):
    def __init__(self, key: Any, value: Any) -> NoReturn:
        self.key = key
        self.value = value


class MerkleNodePlaceInfo(object):
    def __init__(self, level_index: int = 0, item_index: int = 0) -> NoReturn:
        self.level_index = level_index
        self.item_index = item_index

    def left_children(self) -> MerkleNodePlaceInfo:
        return MerkleNodePlaceInfo(self.level_index + 1, self.item_index * 2)

    def right_children(self) -> MerkleNodePlaceInfo:
        return MerkleNodePlaceInfo(self.level_index + 1, self.item_index * 2 + 1)


class MerkleTree(object):

    def __init__(self, hsh: Union[str, Callable[..., Union[bytes, bytearray]]] = 'sha256') -> None:
        if isinstance(hsh, str):
            try:
                if hsh == 'blake3':
                    from blake3 import blake3
                    self.hash_function = blake3
                # elif hsh == 'tigerhash':
                #     from tigerhash import tigerhash
                #     self.hash_function = tigerhash
                else:
                    self.hash_function = getattr(hashlib, hsh)
            except AttributeError:
                raise Exception(f'{hsh} is not supported')
        elif callable(hsh):
            self._get_hash = hsh
        else:
            raise Exception("Incorrect hash argument")

        self.levels = []
        self.leaves = []
        self.leaves_count = 0

    def clear(self) -> NoReturn:
        self.levels = []
        self.leaves = []
        self.leaves_count = 0

    def add_iter(self, keys, values) -> NoReturn:
        for key, value in zip(keys, values):
            self._setitem(key, value, is_build=False)

        self._build()

    def add_dict(self, dct: dict):
        for key in dct:
            self._setitem(key, value=dct[key], is_build=False)

        self._build()

    @property
    def size(self) -> int:
        return self.leaves_count

    @property
    def root_hash(self) -> str:
        return self.levels[0][0].hash

    def _is_last(self, info: MerkleNodePlaceInfo) -> bool:
        return len(self.levels) - 1 == info.level_index

    def _get_node_from_info(self, info: MerkleNodePlaceInfo) -> Optional[MerkleTreeNode]:
        if info.level_index >= len(self.levels) or info.item_index >= len(self.levels[info.level_index]):
            return None

        return self.levels[info.level_index][info.item_index]

    def _get_leaf_from_info(self, info: MerkleNodePlaceInfo) -> Optional[MerkleTreeLeaf]:
        if info.item_index < len(self.leaves):
            return self.leaves[info.item_index]

        return None

    def get_changeset(self, destination: MerkleTree) -> List[dict]:
        source_info = MerkleNodePlaceInfo()
        destination_info = MerkleNodePlaceInfo()
        return self._get_changeset(destination, source_info, destination_info)

    def _get_changeset(self, destination: MerkleTree, source_info: Optional[MerkleNodePlaceInfo],
                       destination_info: Optional[MerkleNodePlaceInfo]) -> List[dict]:
        # Check if mark are given
        if source_info is None:
            if destination._is_last(destination_info):
                # Mark leaf as Created
                destination_leaf = destination._get_leaf_from_info(destination_info)

                if destination_leaf is None:
                    return []

                return [{
                    'Operation type': 'Create',
                    'Key': destination_leaf.key,
                    'Value': destination_leaf.value
                }]
            else:
                # Mark destination subtrees leaves as Created
                destination_left_subtree = destination_info.left_children()
                destination_right_subtree = destination_info.right_children()
                left_inconsistencies = self._get_changeset(destination,
                                                           source_info=None,
                                                           destination_info=destination_left_subtree)
                right_inconsistencies = self._get_changeset(destination,
                                                            source_info=None,
                                                            destination_info=destination_right_subtree)
                return left_inconsistencies + right_inconsistencies

        if destination_info is None:

            if self._is_last(source_info):
                # Mark leaf as Deleted
                source_leaf = self._get_leaf_from_info(source_info)

                if source_leaf is None:
                    return []

                return [{
                    'Operation type': 'Delete',
                    'Key': source_leaf.key,
                    'Value': source_leaf.value
                }]
            else:
                # Mark source subtrees leaves as Deleted
                source_left_subtree = source_info.left_children()
                source_right_subtree = source_info.right_children()
                left_inconsistencies = self._get_changeset(destination,
                                                           source_info=source_left_subtree,
                                                           destination_info=None)
                right_inconsistencies = self._get_changeset(destination,
                                                            source_info=source_right_subtree,
                                                            destination_info=None)
                return left_inconsistencies + right_inconsistencies

        # Get nodes data
        # They will be treated as trees
        # Or handle Nones
        source_node = self._get_node_from_info(source_info)
        destination_node = destination._get_node_from_info(destination_info)

        if destination_node is None and source_node is None:
            return []

        if destination_node is None:
            return self._get_changeset(destination, source_info=source_info, destination_info=None)

        if source_node is None:
            return self._get_changeset(destination, source_info=None, destination_info=destination_info)

        # Check if hashes are equal
        if source_node.hash == destination_node.hash:
            return []

        # Get leaves if node is last in source or destination tree
        source_leaf = None
        destination_leaf = None

        if self._is_last(source_info):
            source_leaf = self._get_leaf_from_info(source_info)

        if destination._is_last(destination_info):
            destination_leaf = destination._get_leaf_from_info(destination_info)

        # Check if source and destination are both leaves
        if source_leaf is not None and destination_leaf is not None:
            if source_leaf.key == destination_leaf.key:
                # Mark leaf as Update
                return [{
                    'Operation type': 'Update',
                    'Key': source_leaf.key,
                    'Source value': source_leaf.value,
                    'Destination value': destination_leaf.value
                }]
            else:
                # Mark source leaf as Deleted and destination leaf as Created
                return [{
                    'Operation type': 'Delete',
                    'Key': source_leaf.key,
                    'Value': source_leaf.value
                }] + \
                       [{
                           'Operation type': 'Create',
                           'Key': destination_leaf.key,
                           'Value': destination_leaf.value
                       }]

        # Compare source leaf with destination tree
        if source_leaf is not None:
            if source_leaf.key <= destination_node.max_left_child:
                # Compare source leaf and left destination subtree
                destination_left_subtree = destination_info.left_children()
                return self._get_changeset(destination, source_info=source_info,
                                           destination_info=destination_left_subtree)
            else:
                # Compare source leaf and right destination subtree
                destination_right_subtree = destination_info.right_children()
                return self._get_changeset(destination, source_info=source_info,
                                           destination_info=destination_right_subtree)

        # Compare Destination leaf with source tree
        if destination_leaf is not None:
            if destination_leaf.key <= source_node.max_left_child:
                # Compare destination leaf and left source subtree
                # Mark source right subtree as Deleted
                source_left_subtree = source_info.left_children()
                return self._get_changeset(destination, source_info=source_left_subtree,
                                           destination_info=destination_info)
            else:
                # Compare destination leaf and right source subtree
                source_right_subtree = source_info.right_children()
                return self._get_changeset(destination, source_info=source_right_subtree,
                                           destination_info=destination_info)

        # Check if keys of one tree are all greater or less then keys of other tree
        if source_node.size < destination_node.size:
            if destination_node.max_left_child < source_node.min_key:
                # Compare source and destination right subtree
                # Destination left subtree mark as Add
                destination_left_subtree = destination_info.left_children()
                destination_right_subtree = destination_info.right_children()
                left_inconsistencies = self._get_changeset(destination,
                                                           source_info=None,
                                                           destination_info=destination_left_subtree)
                right_inconsistencies = self._get_changeset(destination,
                                                            source_info=source_info,
                                                            destination_info=destination_right_subtree)
                return left_inconsistencies + right_inconsistencies

            if destination_node.max_left_child >= source_node.max_key:
                # Compare source and destination left subtree
                # Destination right subtree mark as Add
                destination_left_subtree = destination_info.left_children()
                destination_right_subtree = destination_info.right_children()
                left_inconsistencies = self._get_changeset(destination,
                                                           source_info=source_info,
                                                           destination_info=destination_left_subtree)
                right_inconsistencies = self._get_changeset(destination,
                                                            source_info=None,
                                                            destination_info=destination_right_subtree)
                return left_inconsistencies + right_inconsistencies

        elif source_node.size > destination_node.size:
            if source_node.max_left_child < destination_node.min_key:
                # Compare destination and source right subtree
                # Source left subtree mark Deleted
                source_left_subtree = source_info.left_children()
                source_right_subtree = source_info.right_children()
                left_inconsistencies = self._get_changeset(destination,
                                                           source_info=source_left_subtree,
                                                           destination_info=None)
                right_inconsistencies = self._get_changeset(destination,
                                                            source_info=source_right_subtree,
                                                            destination_info=destination_info)
                return left_inconsistencies + right_inconsistencies

            if source_node.max_left_child >= destination_node.max_key:
                # Compare destination and source left subtree
                # Source right subtree mark Deleted
                source_left_subtree = source_info.left_children()
                source_right_subtree = source_info.right_children()
                left_inconsistencies = self._get_changeset(destination,
                                                           source_info=source_left_subtree,
                                                           destination_info=destination_info)
                right_inconsistencies = self._get_changeset(destination,
                                                            source_info=source_right_subtree,
                                                            destination_info=None)
                return left_inconsistencies + right_inconsistencies

        if source_node.avg == destination_node.avg:
            # Compare left subtrees and right subtrees of destination and source
            destination_left_subtree = destination_info.left_children()
            destination_right_subtree = destination_info.right_children()
            source_left_subtree = source_info.left_children()
            source_right_subtree = source_info.right_children()
            left_inconsistencies = self._get_changeset(destination,
                                                       source_left_subtree,
                                                       destination_left_subtree)
            right_inconsistencies = self._get_changeset(destination,
                                                        source_right_subtree,
                                                        destination_right_subtree)
            return left_inconsistencies + right_inconsistencies

        if source_node.size < destination_node.size:
            # Compare destination and source left and right subtrees
            source_left_subtree = source_info.left_children()
            source_right_subtree = source_info.right_children()
            left_inconsistencies = self._get_changeset(destination,
                                                       source_info=source_left_subtree,
                                                       destination_info=destination_info)
            right_inconsistencies = self._get_changeset(destination,
                                                        source_info=source_right_subtree,
                                                        destination_info=destination_info)
            return left_inconsistencies + right_inconsistencies

        else:
            # Compare source and destination left and right subtrees
            destination_left_subtree = destination_info.left_children()
            destination_right_subtree = destination_info.right_children()
            left_inconsistencies = self._get_changeset(destination,
                                                       source_info=source_info,
                                                       destination_info=destination_left_subtree)
            right_inconsistencies = self._get_changeset(destination,
                                                        source_info=source_info,
                                                        destination_info=destination_right_subtree)
            return left_inconsistencies + right_inconsistencies

    def _get_changeset_legacy(self, destination: MerkleTree):
        result = []
        i = 0
        j = 0

        while i < len(self.leaves) and j < len(destination.leaves):
            if self.leaves[i].key == destination.leaves[j].key and self.leaves[i].value != destination.leaves[j].value:
                result += [{
                    'Operation type': 'Update',
                    'Key': self.leaves[i].key,
                    'Old value': self.leaves[i].value,
                    'Value': destination.leaves[j].value
                }]
                i += 1
                j += 1
            elif self.leaves[i].key < destination.leaves[j].key:
                result += [{
                    'Operation type': 'Delete',
                    'Key': self.leaves[i].key,
                    'Value': self.leaves[i].value
                }]
                i += 1
            else:
                result += [{
                    'Operation type': 'Create',
                    'Key': destination.leaves[j].key,
                    'Value': destination.leaves[j].value
                }]
                j += 1

        return result

    def swap(self, other_tree: MerkleTree) -> NoReturn:
        self.hash_function, other_tree.hash_function = other_tree.hash_function, self.hash_function
        self.leaves, other_tree.leaves = other_tree.leaves, self.leaves
        self.levels, other_tree.levels = other_tree.levels, self.levels
        self.leaves_count, other_tree.leaves_count = other_tree.leaves_count, self.leaves_count

    def _find_position(self, key: Any) -> int:
        min_index = 0
        max_index = len(self.leaves) - 1
        mid_index = (max_index + min_index) // 2

        while max_index >= min_index:
            if self.leaves[mid_index].key == key:
                return mid_index
            elif self.leaves[mid_index].key < key:
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

        if self.leaves[index].key == key:
            return self.leaves[index].value
        else:
            raise Exception("No such element")

    def __getitem__(self, key: Any) -> Any:
        return self.get(key)

    def delete(self, key: Any) -> NoReturn:
        index = self._find_position(key)

        if self.leaves[index].key == key:
            self.leaves.pop(index)
            self.leaves_count -= 1
            self._build()
        else:
            raise Exception("No such element")

    def __delitem__(self, key: Any) -> NoReturn:
        self.delete(key)

    def set(self, key: Any, value: Any) -> NoReturn:
        self._setitem(key, value, is_build=True)

    def __setitem__(self, key: Any, value: Any) -> NoReturn:
        self._setitem(key, value, is_build=True)

    def _setitem(self, key, value: object, is_build: bool):
        index = self._find_position(key)

        if index >= len(self.leaves) or self.leaves[index].key > key:
            self.leaves.insert(index, MerkleTreeLeaf(key, value))
            self.leaves_count += 1
        elif key == self.leaves[index].key:
            self.leaves[index].value = value
        else:
            self.leaves.insert(index + 1, MerkleTreeLeaf(key, value))
            self.leaves_count += 1

        if is_build:
            self._build()

    def _calculate_next_level(self, prev_level: List[MerkleTreeNode]) -> NoReturn:
        new_level = []
        for i in range(1, len(prev_level), 2):
            left = prev_level[i - 1]
            right = prev_level[i]
            new_element = MerkleTreeNode(self._get_hash(left.hash + right.hash), left.size + right.size,
                                         max_key=right.max_key, min_key=left.min_key,
                                         avg=(left.avg + right.avg + 1) // 2,
                                         max_left_child=left.max_key)
            new_level.append(new_element)

        if len(prev_level) % 2 == 1:
            last_element = prev_level[-1]
            new_level.append(MerkleTreeNode(last_element.hash, last_element.size, max_key=last_element.max_key,
                                            min_key=last_element.min_key, avg=last_element.avg,
                                            max_left_child=last_element.max_left_child))

        self.levels = [new_level, ] + self.levels

    def _build(self) -> NoReturn:
        first_level = []
        for leaf in self.leaves:
            new_element = MerkleTreeNode(self._get_hash(leaf.value), size=1, max_key=leaf.key,
                                         min_key=leaf.key, avg=leaf.key, max_left_child=leaf.key)
            first_level.append(new_element)

        self.levels.append(first_level)

        while len(self.levels[0]) > 1:
            self._calculate_next_level(self.levels[0])

    def get_by_order(self, order: int, as_json: bool = False):
        data = {'key': self.leaves[order].key, 'value': self.leaves[order].value}

        if not as_json:
            return data
        else:
            return json.dumps(data)

    def __iter__(self, as_json: bool = False) -> iter:
        for leaf in self.leaves:
            data = {'key': leaf.key, 'value': leaf.value}
            if not as_json:
                yield data
            else:
                yield json.dumps(data)

    def _get_hash(self, value: Any) -> bytearray:
        value = str(value)
        value = value.encode('utf-8')
        hash_value = self.hash_function(value).hexdigest()
        hash_value = bytearray.fromhex(hash_value)
        return hash_value

    def __contains__(self, key: Any) -> bool:
        index = self._find_position(key)

        if index < len(self.leaves) and self.leaves[index].key == key:
            return True
        else:
            return False

    def __len__(self):
        return self.size

    def __eq__(self, o: object) -> bool:
        if type(o) is MerkleTree:
            return self.levels[0][0].hash == o.levels[0][0].hash
        else:
            return False

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __str__(self) -> str:
        # TODO: finish str
        pass

    def verify(self, vo: tuple, hsh="sha256"):
        # TODO: finish verify
        pass
