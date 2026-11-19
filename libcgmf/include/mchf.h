/*------------------------------------------------------------------------------
  CGMF-1.1
  Copyright TRIAD/LANL/DOE - see file LICENSE
  For any questions about CGMF, please contact us at cgmf-help@lanl.gov
-------------------------------------------------------------------------------*/

/*! @file mchf.h

  \brief Monte Carlo Hauser-Feshbach class and prototype definitions

*/

#ifndef __MCHF_H__
#define __MCHF_H__

const int MAX_CASCADE    =    100 ;  /* maximum number of gamma-rays per cascade */
const int MAX_SIMULATION =      1 ;  /* number of Monte Carlo Simulations */

/****************************/
/*    Monte Carlo Index     */
/****************************/
enum class MCPointStatus {
  Uninitialized,
  Valid,
  Unmappable
};

class MCPoint{
 private:
  int    n;    // nucleus index
  int    p;    // CN state parity
  int    j;    // J-array index
  int    k;    // excitation index
  double e;    // excitation energy
  bool   l;    // true if discrete level
  MCPointStatus status;
 public:
  MCPoint(){
    n  = 0;
    p  = 0;
    j  = 0;
    k  = 0;
    e  = 0.0;
    l  = false;
    status = MCPointStatus::Uninitialized;
  }
  MCPoint(int n0, int p0, int j0, int k0, double e0){
    n = n0;
    p = p0;
    j = j0;
    k = k0;
    e = e0;
    l = false;
    status = MCPointStatus::Valid;
  }
  void set(int n0, int p0, int j0, int k0, double e0){
    n = n0;
    p = p0;
    j = j0;
    k = k0;
    e = e0;
    status = MCPointStatus::Valid;
  }
  void setE(double e0){
    e = e0;
  }
  void setDiscrete(){
    l = true;
  }
  void markUnmappable(){
    status = MCPointStatus::Unmappable;
  }
  bool isValid(){
    return status == MCPointStatus::Valid;
  }
  bool isUnmappable(){
    return status == MCPointStatus::Unmappable;
  }
  MCPointStatus getStatus(){
    return status;
  }
  int    getN(){return n;};
  int    getK(){return k;};
  int    getP(){return p;};
  int    getJ(){return j;};
  double getE(){return e;};
  bool   ifDiscrete(){return l;};
};


/****************************/
/*    Particle History      */
/****************************/
class MCHistory{
 private:
  int     id;  // particle identifier
  double  ep;  // emission energy
  MCPoint mp;  // MC index for intermediate state
  MCPoint md;  // direct daughter state
 public:
  MCHistory(){
    id = 0;
    ep = 0.0;
    mp.set(0,0,0,0,0.0);
    md.set(0,0,0,0,0.0);
  }
  MCHistory(int id0, double ep0, MCPoint mp0){
    id = id0;
    ep = ep0;
    mp = mp0;
    md = mp0;
  }
  MCHistory(int id0, double ep0, MCPoint mp0, MCPoint md0){
    id = id0;
    ep = ep0;
    mp = mp0;
    md = md0;
  }
  void set(int id0, double ep0, MCPoint mp0){
    id = id0;
    ep = ep0;
    mp = mp0;
    md = mp0;
  }
  void set(int id0, double ep0, MCPoint mp0, MCPoint md0){
    id = id0;
    ep = ep0;
    mp = mp0;
    md = md0;
  }
  void setEnergy(double ep0){ ep = ep0; }
  int     getIndex()  {return id;};
  double  getEnergy() {return ep;};
  MCPoint getMCPoint(){return mp;};
  MCPoint getDaughterMCPoint(){return md;};
};

#endif //__MCHF_H__
