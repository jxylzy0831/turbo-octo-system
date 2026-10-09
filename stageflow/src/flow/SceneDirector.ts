import type {Snapshot} from '../domain/World';
import {World} from '../domain/World';
import {AudioService} from '../audio/AudioService';
import {ActionRunner} from './ActionRunner';
import type {Beat} from './types';
export class SceneDirector {
  index=0; playing=false; waiting=false; elapsed=0; speed=1;
  private histories=new Map<number,Snapshot>();
  private runner:ActionRunner;
  private manualMotion=false;
  onChange=()=>{};
  onResponse=(text:string)=>{};
  constructor(readonly world:World,readonly beats:Beat[],private audio:AudioService){this.runner=new ActionRunner(world);this.enter(0);}
  get beat(){return this.beats[this.index];}
  get busy(){return this.runner.busy;}
  private enter(index:number){
    this.index=index;this.elapsed=0;this.manualMotion=false;
    this.waiting=this.beat.wait;this.histories.set(index,this.world.snapshot());
    this.runner.start(this.beat.actions);this.audio.play(this.beat.audio);this.onChange();
  }
  update(dt:number){
    if(!this.playing)return;
    const scaled=dt*this.speed;
    this.runner.update(scaled);
    if(this.manualMotion)return;
    if(!this.runner.busy)this.elapsed+=scaled;
    const duration=this.beat.speaker?Math.max(2.8,Math.min(11,this.beat.entry.text.length/6)):2.8;
    if(!this.runner.busy&&!this.audio.busy&&this.elapsed>duration&&!this.waiting){
      if(this.index===this.beats.length-1){this.pause();return;}
      this.enter(this.index+1);
    }
  }
  play(){this.manualMotion=false;this.playing=true;this.audio.resume();this.onChange();}
  pause(){this.playing=false;this.audio.pause();this.onChange();}
  next(){this.pause();this.jump(this.index+1);}
  previous(){this.pause();this.jump(this.index-1);}
  replay(){this.pause();this.jump(this.index);}
  respond(label:string){this.waiting=false;this.elapsed=0;this.onChange();this.onResponse(label);}
  jump(target:number){
    target=Math.max(0,Math.min(this.beats.length-1,target));
    this.audio.stop();this.runner.clear();
    const known=this.histories.get(target);
    if(known){this.world.restore(known);}
    else {
      this.world.reset();
      // 章节跳转还原此前已完成动作，不必观看前面的全部过场。
      for(let i=0;i<target;i++)for(const a of this.beats[i].actions){
        if(a.kind==='move')this.world.actor(a.actor).position=[...a.to];
        if(a.kind==='pose')this.world.actor(a.actor).pose=a.pose;
        if(a.kind==='turn')this.world.actor(a.actor).heading=a.heading;
        if(a.kind==='prop')this.world.actor(a.actor).prop=a.prop;
        if(a.kind==='curtain')this.world.curtain.progress=a.open?1:0;
      }
    }
    this.enter(target);
    // 单步也执行走位；到达后仍保留本条供阅读。
    this.playing=true;this.manualMotion=true;
  }
  finishManualMotion(){if(this.manualMotion&&!this.runner.busy){this.manualMotion=false;this.playing=false;this.elapsed=0;this.onChange();}}
}
