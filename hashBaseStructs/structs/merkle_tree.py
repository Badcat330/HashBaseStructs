import hashlib
from __future__ import annotations
from typing import Any, NoReturn, Sized
from blake3 import blake3


class MerkleTreeNode(object):
    def __init__(self, hash, size, max_key) -> NoReturn:
        self.hash = hash
        self.size = size
        self.max_key = max_key


class MerkleTreeLeave(object):
    def __init__(self, key, value) -> NoReturn:
        self.key = key
        self.value = value

class MerkleNodePlaceInfo(object):
    def __init__(self, level_index=0, item_idex=0) -> NoReturn:
        self.level_index = level_index
        self.item_idex = item_idex  

    def _left_children(self) -> NoReturn:
        self.level_index += 1
        self.item_idex *= 2


    def _right_children(self) -> NoReturn:
        self.level_index += 1
        self.item_idex *= 2 + 1


class MerkleTree(object):

    def __init__(self, hash='sha256') -> NoReturn:
        if isinstance(hash, str):
            try:
                if hash == 'blake3':
                    self.hash_function = blake3
                else:
                    self.hash_function = getattr(hashlib, hash)
            except AttributeError:
                raise Exception(f'{hash} is not supported')
        elif callable(hash):
            self.hash_function = hash
        else:
            raise Exception("Incorrect hash argument")


        self.levels = []
        self.leaves = []
        self.leaves_count = 0

    def clear(self) -> NoReturn:
        self.levels = []
        self.leaves = []
        self.leaves_count = 0

    def add_range(self, keys: list[Any], values: list[Any]) -> NoReturn:
        for key, value in zip(keys, values):
            self._seitem(key, value, is_build=False)

        self._build()
    
    def _is_last(self, info: MerkleNodePlaceInfo) -> bool:
        return self.levels < info.level_index


    def _get_node_from_info(self, info: MerkleNodePlaceInfo) -> MerkleTreeNode:
        if info.level_index >= len(self.levels) and info.item_idex >= len(self.levels[info.level_index]):
            return None
        
        return self.levels[info.level_index][info.item_idex]

    def get_changeset(self, destination: MerkleTree) -> list[dict]:
        source_info = MerkleNodePlaceInfo()
        destination_info = MerkleNodePlaceInfo()
        self._get_changeset(destination, source_info, destination_info)

    def _get_changeset(self, destination: MerkleTree, source_info: MerkleNodePlaceInfo, destination_info: MerkleNodePlaceInfo) -> list[dict]:
        source_node = self._get_node_from_info(source_info)
        destination_node = destination._get_node_from_info(destination_info)
        pass
    

    def swap(self, other_tree: MerkleTree) -> NoReturn:
        self.hash_function, other_tree.hash_function = other_tree.hash_function, self.hash_function
        self.leaves, other_tree.leaves = other_tree.leaves, self.leaves
        self.levels, other_tree.levels = other_tree.levels, self.levels
        self.leaves_count, other_tree.leaves_count = other_tree.leaves_count, self.leaves_count

    def _find_position(self, leaves: list[MerkleTreeLeave], key: Any) -> int:
        min_value = 0
        max_value = len(leaves) - 1
        avg = (min_value + max_value) // 2

        if avg == -1:
            return 0

        while min_value < max_value:
            if leaves[avg].key == key:
                return avg
            elif leaves[avg].key < key:
                return avg + 1 + self._find_position(leaves[avg + 1:], key)
            else:
                return self._find_position(leaves[:avg], key)

        return avg

    def __getitem__(self, key: Any) -> Any:
        index = self._find_position(self.leaves, key)

        if self.leaves[index].key == key:
            return self.leaves[index].value
        else:
            raise Exception("No such element")

    def __delitem__(self, key: Any) -> NoReturn:
        index = self._find_position(self.leaves, key)

        if self.leaves[index].key == key:
            self.leaves.pop(index)
            self.leaves_count -= 1
            self._build()
        else:
            raise Exception("No such element")

    def __setitem__(self, key: Any, value: Any) -> NoReturn:
        self._seitem(key, value, is_build=True)

    def _seitem(self, key, value: object, is_build: bool):
        index = self._find_position(self.leaves, key)

        if index >= len(self.leaves) or self.leaves[index].key > key:
            self.leaves.insert(index, MerkleTreeLeave(key, value))
            self.leaves_count += 1
        elif key == self.leaves[index].key:
            self.leaves[index].value = value
        else:
            self.leaves.insert(index + 1, MerkleTreeLeave(key, value))
            self.leaves_count += 1

        if is_build:
            self._build()

    def _calculate_next_level(self, prev_level: list[MerkleTreeNode]) -> NoReturn:
        new_level = []
        for i in range(1, len(prev_level), 2):
            left = prev_level[i - 1]
            right = prev_level[i]
            new_element = MerkleTreeNode(self._get_hash(left.hash + right.hash), left.size + right.size, right.max_key)
            new_level.append(new_element)

        if len(prev_level) % 2 == 1:
            last_element = prev_level[-1]
            new_level.append(MerkleTreeNode(last_element.hash, last_element.size, last_element.max_key))

        self.levels = [new_level, ] + self.levels

    def _build(self) -> NoReturn:
        first_level = []
        for leafe in self.leaves:
             new_element = MerkleTreeNode(self._get_hash(leafe.value), size=1, max_key=leafe.key)
             first_level.append(new_element)
        
        self.levels.append(first_level)

        while len(self.levels[0]) > 1:
            self._calculate_next_level(self.levels[0])

    def _get_hash(self, value: Any) -> bytearray:
        value = str(value)
        value = value.encode('utf-8')
        hash_value = self.hash_function(value).hexdigest()
        hash_value = bytearray.fromhex(hash_value)
        return hash_value

    def __contains__(self, key: Any) -> bool:
        index = self._find_position(self.leaves, key)

        if index < len(self.leaves) and self.leaves[index].key == key:
            return True
        else:
            return False

    def __len__(self):
        return self.leaves_count

    def __eq__(self, o: object) -> bool:
        if type(o) is MerkleTree:
            return self.levels[0][0].hash == o.levels[0][0].hash
        else:
            return False

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)
