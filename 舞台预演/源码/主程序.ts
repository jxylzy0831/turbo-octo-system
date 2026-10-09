import './样式/应用样式.css';
import script from './数据/演示流程.json';
import {App} from './应用/应用';
const root=document.getElementById('app')!;
try {new App(root,script);}
catch(error){root.textContent='StageFlow 暂时无法启动：'+(error instanceof Error?error.message:String(error))+'。请使用支持 WebGL 的浏览器打开。';}
