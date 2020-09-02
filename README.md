# Calm proxy to launch a Market place

```
http://127.0.0.1:5000/api/v1/mplaunch
```
```
{
    "mpname" : "testmp",
    "mpversion": "0.0.1",
    "projectname": "NTXCHGR018",
    "appname" : "testmp"
}
```
env vars helm install
```
eval $(cat .env | sed 's/^/export /')
helm install -n dev --set ntx.user=$PC_USER,ntx.password=$PC_PASSWORD,ntx.prismcentralhost=$PC_HOST  launchmp launchmp-helm/.
```
