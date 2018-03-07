#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  3 17:30:52 2018

@author: shrey
"""
import csv
csvFile = open('video_result.csv','r')
data = csv.reader(csvFile)
data2 = []
for row in data:
    data2.append(row)
    
print(len(data2))
    
csvFile.close()