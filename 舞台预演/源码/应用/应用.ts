import {World} from '../领域/世界';
import {Choreography} from '../流程/走位编排';
import {SceneDirector} from '../流程/场景调度';
import {ThreeRoomView} from '../渲染/三维房间视图';
import {DialoguePresenter} from '../对话/对话展示';
import {AudioService} from '../音频/音频服务';
import {PlaybackPanel} from '../界面/播放面板';
import type {ScriptData} from '../流程/类型';
export class App {
  constructor(root:HTMLElement,script:ScriptData){
    const panel=new PlaybackPanel(root,script),world=new World(),view=new ThreeRoomView(world,panel.viewport);
    const dialogue=new DialoguePresenter(view,panel.overlay);
    const director=new SceneDirector(world,new Choreography().compile(script),new AudioService());
    director.onChange=()=>{panel.render();dialogue.set(director.beat.speaker,director.beat.entry.text);};
    director.onResponse=text=>dialogue.response(director.beat.waitActor,text);
    panel.bind(director,view);director.onChange();
    let previous=performance.now();
    const frame=(now:number)=>{const dt=Math.min(.05,(now-previous)/1000);previous=now;director.update(dt);director.finishManualMotion();dialogue.update();view.update(dialogue.activeSpeaker,now/1000);requestAnimationFrame(frame);};
    requestAnimationFrame(frame);
  }
}
