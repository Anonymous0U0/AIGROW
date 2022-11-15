import argparse
import collections
import enum
import math
import os
import random
from secrets import choice
import numpy as np

LATCH_LIMIT = 1000000 
AND_LIMIT = 1000000 
INPUT_LIMIT = 1000000

LATCH_RATIO = 1
AND_RATIO = 1
INPUT_RATIO = 1

IS_RE_GEN = False 
BASE_FILE = 'base.aag'
TARGET_FILE = 'target.aag'

class Kind(enum.Enum):
    AND = enum.auto()
    LATCH = enum.auto()   
    INPUT = enum.auto()

class AigerMemory:
    
    @staticmethod
    def compareCur(elem):
        return elem.getElem(0).pos

    
    class relation:
        def __init__(self, am) -> None:
            self.list = []
            self.am = am
            
        def append(self, elem):
            self.list.append(elem)
        
        def __str__(self) -> str:
            line = ''
            line += str(self.nodeToLit(self.list[0], True)) + ' '
            for elem in self.list[1:]:
                if(type(elem) == int):
                    line += str(elem * 2 + random.randint(0,1)) 
                else:
                    line += str(self.nodeToLit(elem, False)) 
                line += ' '
            return line[:-1]
        
        def getElem(self, index: int):
            return self.list[index]
        
        def nodeToLit(self, node: 'TreeNode', lhs: bool) -> int:
            neg = 0
            if lhs == False: neg = node.neg 
            if(node.kind == Kind.INPUT):
                lit = (node.pos + 1) * 2 + neg
            elif(node.kind == Kind.LATCH):
                lit = (self.am.input_num + node.pos + 1) * 2 + neg
            elif(node.kind == Kind.AND):
                lit =  (self.am.input_num + len(self.am.latch_relations) + node.pos + 1) * 2 + neg 
            return lit

    def __init__(self, input_num: int = 0) -> None:
        self.latch_relations = []
        self.and_relations = []
        self.input_num = input_num

    def initialize(self) -> 'TreeNode':
        global BASE_FILE 
        of = open(BASE_FILE, 'r') 
        line = of.readline().split(' ')
        self.input_num = int(line[2])
        self.latch_num = int(line[3])
        self.and_num = int(line[5])
        self.visit_dict = {}

        latch_list = []
        and_list = []

        for _ in range(self.input_num): of.readline()
        for _ in range(self.latch_num): 
            line = of.readline().split(' ') 
            latch_list.append(line)
        outLit = int(of.readline())
        root = self.litToNode(outLit)
        for _ in range(self.and_num):
            line = of.readline().split(' ') 
            and_list.append(line) 
        
        q = collections.deque()
        q.append(root)
        while(len(q)):
            cur = q.popleft()
            if cur.kind == Kind.AND:
                line = and_list[cur.pos]
                node1 = self.litToNode(int(line[1]))
                node2 = self.litToNode(int(line[2]))
                if node1 != None:
                    node1.parent = cur
                    cur.children.append(node1)
                    if node1.is_leaf == False: q.append(node1)
                if node2 != None:
                    node2.parent = cur
                    cur.children.append(node2)
                    if node2.is_leaf == False: q.append(node2)             
            elif cur.kind == Kind.LATCH:
                line = latch_list[cur.pos]
                node = self.litToNode(int(line[1]))
                if node != None:
                    node.parent = cur
                    cur.children.append(node)
                    if node.is_leaf == False: q.append(node)  
            
        return root
        
    def litToNode(self, lit: int ) -> 'TreeNode':
        if lit < ((self.input_num + 1) * 2):
            return None
        elif lit < ((self.latch_num + self.input_num + 1) * 2):
            node = TreeNode(Kind.LATCH, lit//2 - self.input_num - 1)
        else:
            node = TreeNode(Kind.AND, lit//2 - self.input_num - self.latch_num - 1)
        
        if self.visit_dict.get(str(node.kind) + '_' + str(node.pos)) == True:
            node.is_leaf = True
        self.visit_dict[str(node.kind) + '_' + str(node.pos)] = True

        if (lit%2 == 1):
            node.neg = 1
        return node 

    def writeAag(self, file_path: str):
        of = open(file_path, 'w')
        self.latch_num = len(self.latch_relations) 
        self.and_num = len(self.and_relations)
        of.write('aag ' + str(self.input_num + self.latch_num + self.and_num) + ' '
                 + str(self.input_num) + ' '
                 + str(self.latch_num) + ' '
                 + str(1) + ' '
                 + str(self.and_num) + '\n')
        for input in range(self.input_num):
            of.write(str( ( input + 1 ) * 2 ) + '\n')
        
        self.latch_relations.sort(key = self.compareCur)
        self.and_relations.sort(key = self.compareCur)

        for latch in self.latch_relations:
            of.write(str(latch) + '\n')
        of.write(str((self.input_num + self.latch_num + 1) * 2) + '\n')
        for and_gate in self.and_relations:
            of.write(str(and_gate) + '\n')
        of.close()

class TreeNode:
    def __init__(self, kind: Kind = None, pos: int = -1, parent: 'TreeNode' = None, is_leaf: bool = False) -> None:
        self.kind = kind
        self.pos = pos
        self.parent = parent
        self.children = [] # type: list
        self.max_children_num = 0 
        self.descendants = 0
        self.is_leaf = False
        self.neg = 0
        
        if self.kind == Kind.AND:
            self.max_children_num = 2
        elif self.kind == Kind.LATCH:
            self.max_children_num = 1
        elif self.kind == Kind.INPUT:
            self.max_children_num = 0

    def addChild(self, child: 'TreeNode', neg: int = 0) -> bool:
        if len(self.children) >= self.max_children_num : return False
        child.parent = self
        child.neg = neg  # add neg
        self.children.append(child)
    
    def getChild(self, index: int) -> 'TreeNode': 
        if(index > len(self.children)): return None
        return self.children[index] 

    def __str__(self) -> str:
        return str(self.kind.name) + '[' + str(self.pos) + ']'

    def strTree(self) -> str:
        q = collections.deque()
        q.append(self)
        res = ""
        while len(q):
            cur = q.popleft()
            if len(cur.children) == 0: 
                res += ""
                continue
            res = res + str(cur) + " "
            for child in cur.children:
                q.append(child)
                res = res + str(child) + " "
            res += '\n'
        return res
    
    def toAigerMem(self, table: 'VirtualNodeTable', constant_exist: bool = False) -> 'AigerMemory':
        ""
        q = collections.deque()
        q.append(self)
        am = AigerMemory()
        # input_num = 0
        while len(q):
            cur = q.popleft()
            if(cur.is_leaf): continue
            mem = AigerMemory.relation(am)
            mem.append(cur)
            for i in range(cur.max_children_num):
                if i < len(cur.children):
                    q.append(cur.children[i])
                    mem.append(cur.children[i])
                else: #add input or constant
                #     if constant_exist: left = 0
                #     else: left = 1
                    pos = table.newComponent(Kind.INPUT)
                    node = TreeNode(Kind.INPUT, pos, cur, True) 
                    node.neg = random.randint(0,1)
                    mem.append(node)
            if cur.max_children_num == 2:
                am.and_relations.append(mem)
            elif cur.max_children_num == 1:
                am.latch_relations.append(mem)
        am.input_num = table.getComponentNum(Kind.INPUT)
        return am

class VirtualNodeTable:
    def __init__(self) -> None:
        self.components_num = np.array([0] * len(Kind))
    
    def newComponent(self, kind: Kind) -> int:
        "return new component position"
        pos = self.components_num[kind.value - 1]
        self.components_num[kind.value - 1] = pos + 1 
        return pos

    def getComponentNum(self, kind: Kind) -> int:
        "acheive `kind` component number currently"
        return self.components_num[kind.value - 1]
    
class Fuzzer:

    def __init__(self) -> None:
        self.root = TreeNode()
        self.table = VirtualNodeTable()
        self.base_components_num = np.array([0] * len(Kind))

    def initialModel(self) -> None:
        "if re-generation is true, initial based aiger model in memory, else initial the root node"

        if IS_RE_GEN == False:
            self.root = TreeNode(Kind.AND, self.table.newComponent(Kind.AND))
            self.extent_list = [self.root]
        else:
            self.initialAigerModel()
            # print(self.root.strTree())
            
    def initialAigerModel(self) -> 'TreeNode':
        "initial a aiger model based on aag file"
        am = AigerMemory()
        self.root = am.initialize()
        # initial extent_list
        self.extent_list = []
        q = collections.deque()
        q.append(self.root)
        while(len(q)):
            cur = q.popleft()
            if (len(cur.children) < cur.max_children_num) & (cur.is_leaf == False): self.extent_list.append(cur)
            for child in cur.children:
                q.append(child)
        # initial table
        self.table.components_num[Kind.AND.value - 1] = am.and_num
        self.table.components_num[Kind.LATCH.value - 1] = am.latch_num
        # initial base_components_num
        self.base_components_num = np.array([am.and_num, am.latch_num, 0])

    def select(self) -> 'TreeNode':
        "Select a node at random from `extent_list`"
        if len(self.extent_list) == 0:
            return None
        choice = random.randint(1, len(self.extent_list))
        return self.extent_list[choice - 1]

    def selectLeaf(self) -> 'TreeNode':
        "select a leaf node from root"
        cur = self.root
        while(True):
            if cur.is_leaf == True:
                break
            elif len(cur.children) == 0:
                cur = self.root
                continue
            else:
                choice = random.randint(0, len(cur.children) - 1)
                cur = cur.children[choice]
        return cur

    def extent(self, node: 'TreeNode', kind: Kind) -> bool:
        "extent a child for `node`, return false if failure"
        choice = random.randint(0,3) # new component or not
        if (choice > 0) | (self.table.getComponentNum(kind) <= 0):
            child = TreeNode(kind, self.table.newComponent(kind))
            node.addChild(child, random.randint(0,1))
            if child.max_children_num != 0: 
                self.extent_list.append(child)
            return True
        else:
            if(kind != node.kind):
                pos = random.randint(0,self.table.getComponentNum(kind) - 1)
            elif(node.pos + 1 < self.table.getComponentNum(kind)):
                # avoid cyclic definition
                pos = random.randint(node.pos + 1, self.table.getComponentNum(kind) - 1) 
            else: return False
            child = TreeNode(kind, pos, node)
            child.is_leaf = True
            child.neg = random.randint(0,1)
            node.children.append(child)
            return True

    def chooseType(self, input_ratio, latch_ratio, and_ratio):
        choice = random.randint(1,input_ratio + latch_ratio + and_ratio) 
        if(choice <= input_ratio): choice = 3
        elif(choice <= input_ratio + latch_ratio): choice = 2
        else: choice = 1 
        return choice

    def addComponent(self, components_limit: np.array):
        "add `components_limit` components to the model tree, notice it's not nodes but components"
        dist = self.base_components_num + components_limit - self.table.components_num
        
        while( sum(dist > 0) != 0):
            node = self.select() 
            if node == None: break
            # choice = random.randint(0, sum(dist) - 1)
            # for kind in Kind:
            #     choice -= dist[kind.value - 1]
            #     if(choice < 0) : break
            choice = self.chooseType(INPUT_RATIO, LATCH_RATIO, AND_RATIO)
            success = self.extent(node, Kind(choice))
            # print(self.root.strTree())
            if ((success == True) & (len(node.children) == node.max_children_num)):
                self.extent_list.remove(node)
            dist = self.base_components_num + components_limit - self.table.components_num
            flag = False
            for i in dist:
                if i == 0: flag = True
            if flag == True: break
        self.base_components_num = np.array(self.table.components_num)
       

def main():
    
    fuzzer = Fuzzer()
    fuzzer.initialModel()
    fuzzer.addComponent([AND_LIMIT, LATCH_LIMIT, INPUT_LIMIT])
    # print(fuzzer.root.strTree())
    am = fuzzer.root.toAigerMem(fuzzer.table)
    am.writeAag(TARGET_FILE)
    if IS_RE_GEN == 0:
        print("generate " + TARGET_FILE + " successed with " 
                + str(am.input_num) + " inputs, " 
                + str(am.latch_num )+ " latches, " 
                + str(am.and_num) + " ands.")
    else:
        print("reGenerate " + TARGET_FILE + " based on " 
                + BASE_FILE + " successed with " 
                + str(am.input_num) + " inputs, " 
                + str(am.latch_num) + " latches, " 
                + str(am.and_num) + " ands.") 
    # os.popen('/Users/Wendy/cav/gen-aiger/bin/aigtoaig ' + TARGET_FILE + ' ' + TARGET_FILE[:-3] + 'aig')
    
    
        
    
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='GraFuzzer')
    parser.add_argument('--re-generate', type=int, default=IS_RE_GEN,
                        help='whether based on aiger')
    parser.add_argument('--add-latch', type=int, default=LATCH_LIMIT,
                        help='number of LATCHes you want to add')
    parser.add_argument('--add-and', type=int, default=AND_LIMIT,
                        help='number of ANDs you want to add')
    parser.add_argument('--based-file', default=BASE_FILE,
                        help='reGenerate based on this file')
    parser.add_argument('--target-file', default=TARGET_FILE,
                        help='generate as this file')
    parser.add_argument('--input-ratio', default=INPUT_RATIO,
                        help='component ratio of inputs')
    parser.add_argument('--latch-ratio', default=LATCH_RATIO,
                        help='component ratio of latches')
    parser.add_argument('--and-ratio', default=AND_RATIO,
                        help='component ratio of ANG gates')

    args = parser.parse_args()

    IS_RE_GEN = args.re_generate
    
    INPUT_LIMIT = LATCH_LIMIT 
    LATCH_LIMIT = args.add_latch
    AND_LIMIT = args.add_and
    
    INPUT_RATIO = int(args.input_ratio)
    LATCH_RATIO = int(args.latch_ratio)
    AND_RATIO = int(args.and_ratio)



    BASE_FILE = args.based_file 
    
    TARGET_FILE = args.target_file 
    main()