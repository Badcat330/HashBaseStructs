import hashlib


class MerkleTreeNode(object):
        def __init__(self, key, hash):
            self.key = key
            self.hash = hash

class MerkleTreeLeave(MerkleTreeNode):
    def __init__(self, key, hash, value):
        super().__init__(key, hash)
        self.value = value

class MerkleTree(object):
    
    def __init__(self, hash_type='sha256'):
        try:
            if hash_type in ['tiger', 'blake3']:
                pass
            else:
                self.hash_function = getattr(hashlib, hash_type)
        except AttributeError:
            raise Exception(f'{hash_type} is not supported')
        
        self.clear()

    def clear(self):
        self.levels = []
        self.leaves = []
        self.leaves_count = 0

    def add_range(self, keys: list, values: list):
        for key, value in zip(keys, values):
            self._seitem(key, value, is_build=False)

        self.build()

    def get_changeset(self, destination):
        pass

    def swap(self, other_tree):
        buf = self.root
        self.root = other_tree.root
        other_tree.root = buf
        buf = self.leaves_count
        self.leaves_count = other_tree.leaves_count
        other_tree.leaves_count = buf

    def _find_position(self, leaves, key):
        min = 0
        max = len(leaves) - 1
        avg = (min + max) // 2
        
        while min < max:
            if leaves[avg].key == key:
                return leaves[avg].value
            elif leaves[avg].key < key:
                return avg + 1 + self._find_position(leaves[avg+1:], key)
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
        else:
            raise Exception("No such element")
    
    def __setitem__(self, key, value):
        self._seitem(key, value, is_build=True)

    def _seitem(self, key, value: object, is_build: bool):
        index = self._find_position(self.leaves, key)

        if key == self.leaves[index].key:
            self.leaves[index].value = value
            self.leaves[index].hash = self._get_hash(value)
        else:
            self.leaves.insert(index, MerkleTreeLeave(key, self._get_hash(value), value), value)
            self.leaves_count += 1
            
        if is_build:
            self.build()

    def _calculate_next_level(self, prev_level):
        new_level = []
        for i in range(1, prev_level, 2):
            left = prev_level[i-1]
            right = prev_level[i+1]
            new_level.append(MerkleTreeNode(max(left.key, right.key), self._get_hash(left + right)))
        
        if len(prev_level) % 2 == 1:
            last_element = prev_level[-1]
            new_level.append(MerkleTreeNode(last_element.key, last_element.hash))

        self.levels = [new_level, ] + self.levels

        

    def _build(self):
        self._calculate_next_level(self.leaves)
        while len(self.levels[0]) > 1:
            self._calculate_next_level(self.levels[0])

    def _get_hash(self, value):
        value = value.encode('utf-8')
        hash = self.hash_function(value).hexdigest()
        hash = bytearray.fromhex(hash)

    def __contains__(self, item) -> bool:
        index = self._find_position(self.leaves, item)
        
        if self.leaves[index].key == item:
            return True
        else:
            return False

    def __len__(self):
        return self.leaves_count

    def __eq__(self, o: object) -> bool:
        return self.root.hash == o.root.hash

    def __ne__(self, o: object) -> bool:
        return not self.__ne__(o)

    