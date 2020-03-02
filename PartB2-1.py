import pandas as pd
from gurobipy import *
import numpy as np 

#SET flag if the arc data should be biderictional
biderictional = True

#Read data from files
demandData = pd.read_csv("DS9_Network_Node_Data.csv", header = 0, index_col = 0)

nodes = demandData.index.tolist()
demands = demandData.to_dict()['Demand']
group = demandData.to_dict()['Resident Group Number']


N = len(nodes) + 1
Ngroups = 0
for i in nodes:
    if group[i]>Ngroups:
        Ngroups = group[i]
# Assumes groups are numbered with consecutive integers starting from 1
print('Number of groups is ', Ngroups)
groupdemand = []
groupsat = []   #Demand satisfied in solution
for g in range(Ngroups):
    groupdemand.append(0)
    groupsat.append(0)

for i in nodes:
    groupdemand[group[i]-1] += demands[i]   #Indices start from 0 not 1
print("Total demand by group: ", groupdemand)

arcData = pd.read_csv("DS9_Network_Arc_Data_B2.csv", header = 0)
arcs, capacity = multidict({(row[0], row[1]) : row[2] for (index, row) in arcData.iterrows()})
which_bolts, max_bolts = multidict({(row[0], row[1]) : row[3] for (index, row) in arcData.iterrows()})


#Rudimentary data processing to transform into a max flow network


if biderictional:
    for (i,j) in arcs:
        capacity.update({(j, i) : capacity[i,j]})

if biderictional:
    for (i,j) in which_bolts:
        max_bolts.update({(j, i) : max_bolts[i,j]})


        

source = 0
sink = N

capacity.update({(source, 1): sum(demands.values())})
max_bolts.update({(source,1):0})

for node, demand in demands.items():
    capacity.update({(node, sink) : demand})

for node, demand in demands.items():
    max_bolts.update({(node, sink) : demand})


arcs, capacity = multidict(capacity)
which_bolts, max_bolts = multidict(max_bolts)

m = Model('netflow')

# Create variables
flow = m.addVars(arcs, name="flow")
hours_works = m.addVars(which_bolts, vtype=GRB.INTEGER)
improve_cap = m.addVars(which_bolts,name='improve')
did_make_improvement = m.addVars(which_bolts,vtype=GRB.BINARY)

#Set objective
m.setObjective(flow.sum(source,'*'), GRB.MAXIMIZE)

# Arc capacity constraints
#m.addConstrs(
#    (flow[i,j] <= capacity[i,j] for i,j in arcs), "cap")

# Flow conservation constraints
m.addConstrs(
    (flow.sum('*',j) == flow.sum(j,'*') for j in nodes), "node")

m.addConstrs(
        (flow[i,j] <= capacity[i,j] + improve_cap[i,j] for i,j in which_bolts), "max capacity constraint")
m.addConstrs(
        (improve_cap[i,j] <= max_bolts[i,j]*did_make_improvement[i,j] for i,j in which_bolts), "bolts")
m.addConstrs(
        (improve_cap[i,j] >=0 for i,j in which_bolts), "positive # of bolts")
m.addConstrs((flow[i,j]<= capacity[i,j] + improve_cap[i,j] for i,j in which_bolts),"new upper bound")
m.addConstrs((flow[i,j]>= -capacity[i,j] - improve_cap[i,j] for i,j in which_bolts), "new lower bound")

m.addConstrs(hours_works[i,j] == improve_cap[i,j] + 3*did_make_improvement[i,j] for i,j in which_bolts)

#m.addConstrs(hours_works.sum() <=40 for i,j in which_bolts)

# Compute optimal solution
m.write("project.lp")
m.optimize()

# Print solution
if m.status == GRB.Status.OPTIMAL:
    solution = m.getAttr('x', flow)
        
# =============================================================================
#     for i,j in arcs:
#         if solution[i,j] > 0:
#             if j < N and j > 0:
#                 print('%s -> %s: %g' % (i, j, solution[i,j]))
# 
#     for i in nodes:
#         if (i, sink) in arcs and demands[i] > 0 and demands[i]>solution[i,j]:
#             print("Node %s recieved %g out of %g demanded: shortfall %g" % (i, solution[i,j], demands[i],demands[i]-solution[i,j]) )
#         elif (i, sink) in arcs and demands[i] > 0:
#             print("Node %s recieved %g out of %g demanded" % (i, solution[i,j], demands[i]) )
#         #groupsat[group[i]-1] += solution[i,sink]
#     
#     for g in range(Ngroups):
#         if groupdemand[g] > 0:
#             print("Group %s had proportion %g of its demand satisfied" % (g+1, groupsat[g]/groupdemand[g]))
# print(hours_works)
# =============================================================================

