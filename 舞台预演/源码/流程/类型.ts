import type {ActorId,Position,Pose} from '../领域/世界';
export interface Entry { id:string; label:string; text:string }
export interface ScriptScene { title:string; subtitle:string; entries:Entry[] }
export interface ScriptData { source:string; scenes:ScriptScene[] }
export type Action =
  | {kind:'move'; actor:ActorId; to:Position; seconds?:number}
  | {kind:'pose'; actor:ActorId; pose:Pose}
  | {kind:'turn'; actor:ActorId; heading:number}
  | {kind:'curtain'; open:boolean; seconds?:number}
  | {kind:'prop'; actor:ActorId; prop:string};
export interface Beat { scene:number; entry:Entry; speaker?:ActorId; actions:Action[]; wait:boolean; waitActor:ActorId; audio?:string }
