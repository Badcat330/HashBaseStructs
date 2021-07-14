import hashlib
from blake3 import blake3


class MerkleTreeNode(object):
    def __init__(self, hash_value=None):
        self.hash = hash_value


class MerkleTreeLeave(MerkleTreeNode):
    def __init__(self, key, value):
        super().__init__()
        self.key = key
        self.value = value

class MerkleSerchInfo(object):
    def __init__(self, level_index, item_idex, size):
        self.level_index = level_index
        self.item_idex = item_idex
        self.size = size
        


class MerkleTree(object):

    def __init__(self, hash_type='sha256'):
        try:
            if hash_type == 'blake3':
                self.hash_function = blake3
            else:
                self.hash_function = getattr(hashlib, hash_type)
        except AttributeError:
            raise Exception(f'{hash_type} is not supported')

        self.levels = []
        self.leaves = []
        self.leaves_count = 0

    def clear(self):
        self.levels = []
        self.leaves = []
        self.leaves_count = 0

    def add_range(self, keys: list, values: list):
        for key, value in zip(keys, values):
            self._seitem(key, value, is_build=False)

        self._build()

    def _get_level_node(self, level_index, item_index):
        if level_index < len(self.levels) and item_index < len(self.levels[level_index]):
            return self.levels[level_index][item_index]
        else:
            return None

    def get_changeset(self, destination):
        source_info = MerkleSerchInfo(0, 0, self.leaves_count)
        destination_info = MerkleSerchInfo(0, 0, destination.leaves_count)
        self._get_changeset(destination, source_info, destination_info)

    def _get_changeset(self, destination, source_info: MerkleSerchInfo, destination_info: MerkleSerchInfo):
        if destination_info.size > source_info.size:
            left_subtree_size = 2 ** (len(destination.levels) - 2)
            destination_info_left = MerkleSerchInfo(destination_info.level_index + 1, destination_info.item_idex * 2, left_subtree_size)
            destination_info_right = MerkleSerchInfo(destination_info.level_index + 1, destination_info.item_idex * 2 + 1, 
                                                     destination_info.size - left_subtree_size)
            return self.get_changeset(destination, source_info, destination_info_left) + \
                   self.get_changeset(destination, source_info, destination_info_right)
        elif destination_info.size < source_info.size:
            left_subtree_size = 2 ** (len(self.levels) - 2)
            source_info_left = MerkleSerchInfo(source_info.level_index + 1, source_info.item_idex * 2, left_subtree_size)
            source_info_right = MerkleSerchInfo(source_info.level_index + 1, source_info.item_idex * 2 + 1, 
                                                     source_info.size - left_subtree_size)
            return self.get_changeset(destination, source_info_left, destination_info) + \
                   self.get_changeset(destination, source_info_right, destination)
        else:
            pass

            


    def swap(self, other_tree):
        self.hash_function, other_tree.hash_function = other_tree.hash_function, self.hash_function
        self.leaves, other_tree.leaves = other_tree.leaves, self.leaves
        self.levels, other_tree.levels = other_tree.levels, self.levels
        self.leaves_count, other_tree.leaves_count = other_tree.leaves_count, self.leaves_count

    def _find_position(self, leaves, key):
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

    def __getitem__(self, key):
        index = self._find_position(self.leaves, key)

        if self.leaves[index].key == key:
            return self.leaves[index].value
        else:
            raise Exception("No such element")

    def __delitem__(self, key):
        index = self._find_position(self.leaves, key)

        if self.leaves[index].key == key:
            self.leaves.pop(index)
            self.leaves_count -= 1
            self._build()
        else:
            raise Exception("No such element")

    def __setitem__(self, key, value):
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

    def _calculate_next_level(self, prev_level):
        new_level = []
        for i in range(1, len(prev_level), 2):
            left = prev_level[i - 1]
            right = prev_level[i]
            new_element = MerkleTreeNode(self._get_hash(left.hash + right.hash))
            new_level.append(new_element)

        if len(prev_level) % 2 == 1:
            last_element = prev_level[-1]
            new_level.append(MerkleTreeNode(last_element.hash))

        self.levels = [new_level, ] + self.levels

    def _build(self):
        first_level = []
        for leave in self.leaves:
             new_element = MerkleTreeNode(self._get_hash(leave.value))
             first_level.append(new_element)
        
        self.levels.append(first_level)

        while len(self.levels[0]) > 1:
            self._calculate_next_level(self.levels[0])

    def _get_hash(self, value):
        value = str(value)
        value = value.encode('utf-8')
        hash_value = self.hash_function(value).hexdigest()
        hash_value = bytearray.fromhex(hash_value)
        return hash_value

    def __contains__(self, item) -> bool:
        index = self._find_position(self.leaves, item)

        if index < len(self.leaves) and self.leaves[index].key == item:
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
