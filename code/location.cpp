#include<bits/stdc++.h>
using namespace std;
typedef long long ll;
const int INF=0x3f3f3f3f;
const long long mod=100000007;
const double e=2.718281828459045;
const double pi=acos(-1.0);
#define CK cout<<"OK\n";
int n;
int main(){
	freopen("input1.txt","r",stdin);
	freopen("output1.txt","w",stdout);
	scanf("%d",&n);
	for(int i=0;i<n;i++){
		string s,s1,s2;
		cin>>s;
		if(s[0]=='u')s="0,0";
		for(int j=0;j<s.length();j++){
			if(s[j]==','){
				s1=s.substr(0,j);
				s2=s.substr(j+1);
				cout<<s1<<"\t"<<s2<<endl;
			}
		}
	}
	return 0;
	//freopen("CON","r",stdin); //切换到从控制台输入
}
