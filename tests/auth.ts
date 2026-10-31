export const auth:{user:{userId:string;displayName:string;email:string}|null}={user:null};
export async function getChatGPTUser(){return auth.user;}
