import {World} from '../domain/World';
import {Choreography} from '../flow/Choreography';
import {SceneDirector} from '../flow/SceneDirector';
import {ThreeRoomView} from '../rendering/ThreeRoomView';
import {DialoguePresenter} from '../dialogue/DialoguePresenter';
import {AudioService} from '../audio/AudioService';
import {PlaybackPanel} from '../ui/PlaybackPanel';
import type {ScriptData} from '../flow/types';
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
