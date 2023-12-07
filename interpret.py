import re
import argparse
import sys
import xml.etree.ElementTree as et

class nil:
    def __init__(self, value):
        self.value = value

class Instruction:
    def __init__(self, opcode, number):
        self.opcode = opcode.upper()
        self.number = number
        self.args = []

    def add_arg(self, value , arg_type):
        self.args.append(Argument(value, arg_type))

    def get_op(self):
        return self.opcode
    
    def get_num(self):
        return self.number
    
    def get_args(self):
        return self.args
    
class Argument:
    def __init__(self, value, typ):
        self.value = value
        self.typ = typ

    def arg_value(self):
        return self.value
    
    def arg_type(self):
        return self.typ
    
GF_dict = {}

TF_dict = {}
TF_exists = False

LF_dict = {}
LF_exists = False
LF_stack = []

stack = []

label_dict = {}

call_stack = []

def main():
    source, input = parse_args()
    instructions, input = parse_xml(source, input)
    handle_instructions(instructions, input)
    exit(0)

def print_help():
    print("zde bude usage...")
    exit(0)

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', help='An optional integer argument', action='store_true')
    parser.add_argument('--source', help='An optional integer argument', type=str)
    parser.add_argument('--input', help='An optional integer argument', type=str)

    args = parser.parse_args()

    if(args.help):
        print_help()

    if(args.input == None and args.source == None):
        print("Je potreba zadat alespon jeden z argumentu --source nebo --input")
        exit(10)

    if(args.input == None):
        input = input_file(args.input, "stdin")
        source = source_file(args.source, "file")
    elif(args.source == None):
        input = input_file(args.input, "file")
        source = source_file(args.source, "stdin")
    else:
        input = input_file(args.input, "file")
        source = source_file(args.source, "file")

    return source,input

def input_file(path, case):
    try:
        if case == "stdin":
            input = sys.stdin.read()
        else:
            with open(path, 'r') as f:
                input = f.read()
    except:
        exit(11)

    return input

def source_file(path, case):
    try:
        if case == "stdin":
            source = et.parse(sys.stdin)
        else:
            source = et.parse(path)
    except Exception as e:
        exit(31)

    return source

def parse_xml(source, input):

    #kontrola hlavičky xml
    main = source.getroot()
    if(main.tag != "program" or main.attrib['language'] != "IPPcode23"):
        exit(32)

    #kontrola instrukcí a argumentů
    for instruction in main:
        if(instruction.tag != "instruction"):
            exit(32)    
    
        attr = list(instruction.attrib.keys())
        if ("order" in attr or "opcode" in attr):
            pass
        else:
            exit(32)

        if not(re.match(r"\d", instruction.attrib["order"])):
            exit(32)
        
        for i in instruction:
            if not(re.match(r"arg[123]", i.tag)):
                exit(32)
    
    #seřazení instrukcí a argumentů
    main = sorted(main, key=lambda child: int(child.get('order')))
    for instruction in main:
        args = sorted(instruction.findall('*'), key=lambda x: x.tag)
        for i in args:
            instruction.remove(i)
        for i in args:
            instruction.append(i)

    #seznam instrukcí programu a jejich rozdělení do tříd
    instructions = []
    for instruction in main:
        c = Instruction(instruction.attrib["opcode"], instruction.attrib["order"])
        instructions.append(c)
        for i in instruction:
            try:
                text = str(i.text).strip()
                text = escape_replace(text)
                c.add_arg(text, str(i.attrib["type"]).strip())
            except Exception as e:
                exit(32)

    return instructions, input
    
def handle_instructions(instruction_list, input):
    input = input.splitlines()
    #první průchod pro načtení a uložení instrukcí LABEL
    j = 0
    while j < len(instruction_list):
        opcode = instruction_list[j]
        argument_list = opcode.get_args()
        match str(opcode.get_op()).upper():
            case "LABEL":
                if(argument_list[0].arg_value() in label_dict):
                    exit(52)
                label_dict[get_value(argument_list[0].arg_type(),argument_list[0].arg_value())] = j
            case _:
                pass
        j += 1

    #cyklení přes jednotlivé instrukce v seznamu a jejich zpracování
    i = 0
    while i < len(instruction_list):
        global TF_exists
        global LF_exists
        global GF_dict
        global TF_dict
        global LF_dict
        opcode = instruction_list[i]
        
        argument_list = opcode.get_args()
        match str(opcode.get_op()).upper():
            case "DEFVAR":
                if(def_exists(argument_list[0].arg_value())):
                    exit(52)
                move_var(argument_list[0].arg_value(), "", None)

            case "MOVE":
                if not (var_exists(argument_list[0].arg_value())):
                    exit(54)
                if(argument_list[1].arg_type() == "var"):
                    if not (var_exists(argument_list[1].arg_value())):
                        exit(54)
                    if(get_value(argument_list[1].arg_type(), argument_list[1].arg_value()) == None):
                        exit(56)
                    add_var(argument_list[0].arg_value(), get_value(argument_list[1].arg_type(),argument_list[1].arg_value()))
                else:
                    move_var(argument_list[0].arg_value(), argument_list[1].arg_value(), get_type(argument_list[1].arg_type(),argument_list[1].arg_value()))

            case "CREATEFRAME":
                if (TF_exists == True):
                    TF_dict = {}
                TF_exists = True

            case "PUSHFRAME":

                if(TF_exists == False):
                    exit(55)
                if(LF_exists == True):
                    LF_stack.append(LF_dict)

                LF_dict = TF_dict
                temp = {}
                for old_key in LF_dict:
                    new_key = old_key.replace('TF', 'LF')
                    temp[new_key] = LF_dict[old_key]

                LF_exists = True
                LF_dict = temp

                TF_exists = False
                TF_dict = {}

            case "POPFRAME":
                if(LF_exists == False):
                    exit(55)

                TF_dict = LF_dict
                temp = {}
                for old_key in TF_dict:
                    new_key = old_key.replace('LF', 'TF')
                    temp[new_key] = TF_dict[old_key]
                TF_dict = temp

                if(len(LF_stack) > 0):
                    LF_dict = LF_stack.pop()
                    LF_exists = True
                else:
                    LF_dict = {}
                    LF_exists = False

                TF_exists = True

            case "CALL":
                if(argument_list[0].arg_value() not in label_dict):
                    exit(52)
                call_stack.append(i)
                i = label_dict[argument_list[0].arg_value()]

            case "RETURN":
                if(len(call_stack) == 0):
                    exit(56)
                i = call_stack.pop(-1)

            #Práce s datovým zásobníkem
            case "PUSHS":
                result = get_value(argument_list[0].arg_type(),argument_list[0].arg_value())
                stack.append(result)

            case "POPS":
                if(len(stack) == 0):
                    exit(56)
                add_var(argument_list[0].arg_value(), stack.pop(-1))

            #Aritmetické, relační, booleovské a konverzní instrukce
            case "ADD":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != int or type(operands[1]) != int):
                    exit(53)
                result = operands[0] + operands[1]
                add_var(argument_list[0].arg_value(), result)       
            case "SUB":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != int or type(operands[1]) != int):
                    exit(53)
                result = operands[0] - operands[1]
                add_var(argument_list[0].arg_value(), result)
            case "MUL":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != int or type(operands[1]) != int):
                    exit(53)
                result = operands[0] * operands[1]
                add_var(argument_list[0].arg_value(), result)
            case "IDIV":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != int or type(operands[1]) != int):
                    exit(53)
                if(operands[1] == 0):
                    exit(57)
                result = operands[0] / operands[1]
                add_var(argument_list[0].arg_value(), int(result))
            case "LT":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != type(operands[1])):
                    exit(53)
                if(type(operands[0]) == nil):
                    exit(53)
                if(operands[0] < operands[1]):
                    add_var(argument_list[0].arg_value(), True)
                else:
                    add_var(argument_list[0].arg_value(), False)
                    
            case "GT":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != type(operands[1])):
                    exit(53)
                if(type(operands[0]) == nil):
                    exit(53)
                if(operands[0] > operands[1]):
                    add_var(argument_list[0].arg_value(), True)
                else:
                    add_var(argument_list[0].arg_value(), False)
            case "EQ":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                op0 = type(operands[0])
                op1 = type(operands[1])
                if(op0 == nil and op1 == nil):
                    add_var(argument_list[0].arg_value(), True)
                elif(op0 == nil or op1 == nil):
                    add_var(argument_list[0].arg_value(), False)
                else:
                    if(op0 != op1):
                        exit(53)
                    if(operands[0] == operands[1]):
                        add_var(argument_list[0].arg_value(), True)
                    else:
                        add_var(argument_list[0].arg_value(), False)

            case "AND":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != bool or type(operands[1]) != bool):
                    exit(53)
                result = (operands[0] and operands[1])
                add_var(argument_list[0].arg_value(), result)

            case "OR":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != bool or type(operands[1]) != bool):
                    exit(53)
                result = (operands[0] or operands[1])
                add_var(argument_list[0].arg_value(), result)

            case "NOT":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None):
                    exit(56)
                if(type(operands[0]) != bool):
                    exit(53)
                result = (not operands[0])
                add_var(argument_list[0].arg_value(), result)

            case "INT2CHAR":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None):
                    exit(56)
                if(type(operands[0]) != int):
                    exit(53)
                try:
                    result = chr(operands[0])
                except:
                    exit(58)
                add_var(argument_list[0].arg_value(), result)

            case "STRI2INT":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != str or type(operands[1]) != int):
                    exit(53)
                try:
                    result = ord(operands[0][operands[1]])
                except:
                    exit(58)
                add_var(argument_list[0].arg_value(), result)

            #Vstupně-výstupní instrukce
            case "WRITE":
                value = argument_list[0].arg_value()
                typ = argument_list[0].arg_type()
                if(value == "nil"):
                    pass

                elif(typ == "string"):
                    print(str(value), end="")

                elif(typ == "var"):
                    if not (var_exists(argument_list[0].arg_value())):
                        exit(52)

                    if(get_value(typ, value) == None):
                        exit(56)
                             
                    write_var(argument_list[0].arg_value())

                else:
                    print(value, end="")

            case "READ":
                operands = valid_arit(argument_list, 0)
                typ = str(argument_list[1].arg_value())
                if typ not in ["int","string","bool"]:
                    exit(32)
                if(len(input) == 0):
                    result = nil("nil")
                else:
                    try:
                        match typ:
                            case "int":
                                result = int(input.pop(0))
                            case "string":
                                result = str(input.pop(0))
                            case "bool":
                                result = input.pop(0)
                                if result == "true":
                                    result = bool(result)
                                else:
                                    result = bool(0)
                            case _:
                                exit(32)
                    except Exception as e:
                        result = nil("nil")
                add_var(argument_list[0].arg_value(), result)

            #Práce s řetězci
            case "CONCAT":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != str or type(operands[1]) != str):
                    exit(53)
                result = operands[0] + operands[1]
                add_var(argument_list[0].arg_value(), result)
            case "STRLEN":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None):
                    exit(56)
                if(type(operands[0]) != str):
                    exit(53)
                if(operands[0] == "None"):
                    result = 0
                else:
                    result = len(operands[0])
                add_var(argument_list[0].arg_value(), result)
            case "GETCHAR":
                operands = valid_arit(argument_list, 1)
                if(operands[0] == None or operands[1] == None):
                    exit(56)
                if(type(operands[0]) != str or type(operands[1]) != int):
                    exit(53)
                try:
                    result = (operands[0][operands[1]])
                except:
                    exit(58)
                add_var(argument_list[0].arg_value(), result)

            case "SETCHAR":
                operands = valid_arit(argument_list, 0)
                if(operands[0] == None or operands[1] == None or operands[2] == None):
                    exit(56)
                if(type(operands[0]) != str or type(operands[1]) != int or type(operands[2]) != str):
                    exit(53)
                string = operands[0]
                at = operands[1]
                replace = operands[2][0]
                if(at > len(string) or at < 0):
                    exit(58)
                try:
                    result = string[:at] + replace + string[at+1:]
                except:
                    exit(58)
                add_var(argument_list[0].arg_value(), result)

            #Práce s typy
            case "TYPE":
                operands = valid_arit(argument_list, 1)
                result = type(operands[0])
                if(result == int):
                    result = str("int")
                elif(result == bool):
                    result = str("bool") 
                elif(result == nil):
                    result = str("nil") 
                elif(result == str):
                    result = str("string")
                else:
                    result = str("")
                move_var(argument_list[0].arg_value(), result, str)
                
            #Instrukce pro řízení toku programu
            case "LABEL":
                pass

            case "JUMP":
                if(argument_list[0].arg_value() not in label_dict):
                    exit(52)
                i = label_dict[argument_list[0].arg_value()]

            case "JUMPIFEQ":
                operands = valid_labels(argument_list)
                val1 = operands[1]
                val2 = operands[2]
                if(val1 == None or val2 == None):
                    exit(56)
                if(type(val1) == nil or type(val2) == nil):
                    if(type(val1) == nil and type(val2) == nil):
                        i = label_dict[argument_list[0].arg_value()]
                else:
                    if(type(val1) != type(val2)):
                        exit(53)
                    if(get_value(argument_list[1].arg_type(), argument_list[1].arg_value()) == get_value(argument_list[2].arg_type(), argument_list[2].arg_value())):
                        i = label_dict[argument_list[0].arg_value()]

            case "JUMPIFNEQ":
                operands = valid_labels(argument_list)
                val1 = operands[1]
                val2 = operands[2]
                if(val1 == None or val2 == None):
                    exit(56)
                if(type(val1) == nil or type(val2) == nil):
                    if not (type(val1) == nil and type(val2) == nil):
                        i = label_dict[argument_list[0].arg_value()]
                else:
                    if(type(val1) != type(val2)):
                        exit(53)
                    if(get_value(argument_list[1].arg_type(), argument_list[1].arg_value()) != get_value(argument_list[2].arg_type(), argument_list[2].arg_value())):
                        i = label_dict[argument_list[0].arg_value()]

            case "EXIT":
                operands = valid_arit(argument_list, 0)
                if(type(operands[0]) != int):
                    exit(53)
                if(operands[0] < 0 or operands[0] > 49):
                    exit(57)
                else:
                    exit(operands[0])
        i += 1

#Pomocná funkce pro validaci argumentů instrukcí začínajících proměnnou
def valid_arit(argument_list, index_from):
    j = 0
    operands = []
    while j < len(argument_list):
        val = argument_list[j].arg_value()
        if(argument_list[j].arg_type() == "var"):
            if not (var_exists(val)):
                exit(52)
        if j > index_from - 1:
            operands.append(get_value(argument_list[j].arg_type(), val))
        j+=1

    return operands 

#Pomocná funkce pro validaci argumentů instrukce LABEL
def valid_labels(argument_list):
    j = 0
    operands = []
    while j < len(argument_list):
        val = argument_list[j].arg_value()
        if(argument_list[j].arg_type() == "var"):
            if not (var_exists(val)):
                exit(52)
        if j == 0:
            if(argument_list[j].arg_value() not in label_dict):
                exit(52)
        operands.append(get_value(argument_list[j].arg_type(), val))
        j+=1

    return operands 

#Pomocná funkce pro zjištění existence proměnné
def var_exists(var):
    typ = str(var)[:2]
    exists = False  
    match typ:
        case "GF":
            if(var in GF_dict):
                exists = True
            else:
                exit(54)
        case "TF":
            if TF_exists == False:
                exit(55)
            if(var in TF_dict):
                exists = True
            else:
                exit(54)
        case "LF":
            if LF_exists == False:
                exit(55)
            if(var in LF_dict):
                exists = True
            else:
                exit(54)
        case _:
            exit(32) 
    return exists 

#Pomocná funkce pro zjištění existence proměnné pro instrukci DEFVAR
def def_exists(var):
    typ = str(var)[:2]
    exists = False  
    match typ:
        case "GF":
            if(var in GF_dict):
                exists = True
        case "TF":
            if TF_exists == False:
                exit(52)
            if(var in TF_dict):
                exists = True
        case "LF":
            if LF_exists == False:
                exit(52)
            if(var in LF_dict):
                exists = True
        case _:
            exit(32) 
    return exists 

#Pomocná funkce pro přidání proměnné do slovníku
def add_var(var, value):
    ramec = str(var)[:2]
    match ramec:
        case "GF":
            GF_dict[var] = value
        case "TF":
            TF_dict[var] = value    
        case "LF":
            LF_dict[var] = value

#Pomocná funkce pro přetypování a uožení proměnné so dlovníku
def move_var(var, value, typ):
    ramec = str(var)[:2]
    match ramec:
        case "GF":
            if typ == int:
                GF_dict[var] = int(value)
            elif typ == str:
                GF_dict[var] = str(value)
            elif typ == bool:
                if(value == "true"):
                   GF_dict[var] = bool(value)
                if(value == "false"):
                    GF_dict[var] = bool(0)
            elif typ == nil:
                GF_dict[var] = nil(value)
            elif typ == None:
                GF_dict[var] = None
            else:
                pass
                #print("co tu delam?")
        case "TF":
            if typ == int:
                TF_dict[var] = int(value)
            elif typ == str:
                TF_dict[var] = str(value)
            elif typ == bool:
                if(value == "true"):
                   TF_dict[var] = bool(value)
                if(value == "false"):
                    TF_dict[var] = bool(0)
            elif typ == nil:
                TF_dict[var] = nil(value)
            elif typ == None:
                TF_dict[var] = None
            else:
                pass
                #print("co tu delam?")
        case "LF":
            if typ == int:
                LF_dict[var] = int(value)
            elif typ == str:
                LF_dict[var] = str(value)
            elif typ == bool:
                if(value == "true"):
                   LF_dict[var] = bool(value)
                if(value == "false"):
                    LF_dict[var] = bool(0)
            elif typ == nil:
                LF_dict[var] = nil(value)
            elif typ == None:
                LF_dict[var] = None
            else:
                pass
                #print("co tu delam?")
        case _:
            exit(32)
    return

#Pomocná funkce pro zjištění hodnoty a typu proměnné či konstanty
def get_value(typ, value):
    if(typ != "var"):
        match typ:
            case "int":
                return int(value)
            case "bool":
                if(value == "true"):
                    return bool(value)
                else:
                    return bool(0)
            case "string":
                return str(value)
            case "nil":
                return nil(value)
            case "label":
                return str(value)
    else: 
        match str(value)[:2]:
            case "GF":
                return GF_dict[value]
            case "TF":
                return TF_dict[value]
            case "LF":
                return LF_dict[value]
            case _:
                exit(32)

#Pomocná funkce pro zjištění typu argumentu
def get_type(typ, value):
    match typ:
        case "int":
            return int
        case "string":
            return str
        case "bool":
            return bool
        case "nil":
            return nil
        case "var":
            if(str(value)[:2] == "GF"):
                return type(GF_dict[value])
            if(str(value)[:2] == "LF"):
                return type(LF_dict[value])
            if(str(value)[:2] == "TF"):
                return type(TF_dict[value])
        case _:
            exit()

#Pomocná funkce pro vypsání argumentu na STDOUT
def write_var(var):
    typ = str(var)[:2]
    match typ:
        case "GF":
            if(type(GF_dict[var]) == bool):
                print(str(GF_dict[var]).lower(), end="")
            elif(type(GF_dict[var]) == nil):
                pass
            elif(type(GF_dict[var]) == int):
                print(GF_dict[var], end="")
            elif(type(GF_dict[var]) == str):
                print(str(GF_dict[var]), end="")
            else:
                pass
        case "TF":
            if(type(TF_dict[var]) == bool):
                print(str(TF_dict[var]).lower(), end="")
            elif(type(TF_dict[var]) == nil):
                pass
            elif(type(TF_dict[var]) == int):
                print(TF_dict[var], end="")
            elif(type(TF_dict[var]) == str):
                print(str(TF_dict[var]), end="")
            else:
                pass
        case "LF":
            if(type(LF_dict[var]) == bool):
                print(str(LF_dict[var]).lower(), end="")
            elif(type(LF_dict[var]) == nil):
                pass
            elif(type(LF_dict[var]) == int):
                print(LF_dict[var], end="")
            elif(type(LF_dict[var]) == str):
                print(str(LF_dict[var]), end="")
            else:
                pass
        case _:
            exit(32)

#Pomocná funkce pro přepsání escape sekvencí
def escape_replace(text):
    i = 0
    while(text.find('\\') != -1):
        i = str.find(text, '\\', i)
        if(text[i+1].isdigit() and text[i+2].isdigit() and text[i+3].isdigit()):
            text = text[:i] + chr(int(text[i+1:i+4])) + text[i+4:]
        else:
            i += 1
    return text

if __name__ == "__main__":
    main()