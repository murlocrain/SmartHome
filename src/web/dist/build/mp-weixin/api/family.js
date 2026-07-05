"use strict";const e=require("./index.js");exports.createFamily=t=>e.request({url:"/family/create",method:"POST",data:t}),exports.getFamilyList=()=>e.request({url:"/family/list",method:"GET"});
