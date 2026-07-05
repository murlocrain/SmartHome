"use strict";require("../common/vendor.js");const e=require("./index.js");exports.aiAgentControl=r=>e.request({url:"/agent/control",method:"POST",data:{message:r}});
