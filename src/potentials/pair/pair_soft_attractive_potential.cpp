/* *************************************************************
 *  
 *   Active Particles on Curved Spaces (APCS)
 *   
 *   Author: Rastko Sknepnek
 *  
 *   Division of Physics
 *   School of Engineering, Physics and Mathematics
 *   University of Dundee
 *   
 *   (c) 2013
 *   
 *   This program cannot be used, copied, or modified without
 *   explicit permission of the author.
 * 
 * ************************************************************* */

/*!
 * \file pair_soft_attractive_potential.cpp
 * \author Rastko Sknepnek, sknepnek@gmail.com
 * \date 18-May-2015
 * \brief Implementation of PairSoftAttractivePotential class
 */ 

#include "pair_soft_attractive_potential.hpp"

//! \param dt time step sent by the integrator 
void PairSoftAttractivePotential::compute(double dt)
{
  int N = m_system->size();
  double k = m_k;
  double ai, aj;
  double force_factor;
  double alpha = 1.0;  // phase in factor
  
  if (m_system->compute_per_particle_energy())
  {
    for  (int i = 0; i < N; i++)
    {
      Particle& p = m_system->get_particle(i);
      p.set_pot_energy("soft_attractive",0.0);
    }
  }
  
  m_potential_energy = 0.0;
  for  (int i = 0; i < N; i++)
  {
    Particle& pi = m_system->get_particle(i);
    if (m_phase_in)
      alpha = m_val->get_val(static_cast<int>(pi.age/dt));
    ai = pi.get_radius();
    vector<int>& neigh = m_nlist->get_neighbours(i);
    for (unsigned int j = 0; j < neigh.size(); j++)
    {
      Particle& pj = m_system->get_particle(neigh[j]);
      k = m_pair_params[pi.get_type()-1][pj.get_type()-1].k;
      double fact = m_pair_params[pi.get_type()-1][pj.get_type()-1].fact;
      aj = pj.get_radius();
      double dx = pj.x - pi.x, dy = pj.y - pi.y, dz = pj.z - pi.z;
      m_system->apply_periodic(dx,dy,dz);
      double r_sq = dx*dx + dy*dy + dz*dz;
      double r = sqrt(r_sq);
      double ai_p_aj;
      if (!m_use_particle_radii)
        ai_p_aj = m_pair_params[pi.get_type()-1][pj.get_type()-1].a;
      else
        ai_p_aj = ai+aj;
      double r_turn = fact*ai_p_aj;
      double r_f = 2.0*r_turn - ai_p_aj;
      double diff;
      double pot_eng;
      if (r < r_f)
      {
        if (r <= r_turn)
        {
          diff = ai_p_aj - r;
          pot_eng = 0.5*k*alpha*diff*diff;
          if (r > 0.0) force_factor = k*alpha*diff/r;
          else force_factor = k*diff;
        }
        else if (r > r_turn && r < r_f)
        {
          diff = r_f - r;
          pot_eng = -0.5*k*alpha*diff*diff;
          force_factor = -k*alpha*diff/r;
        }
        m_potential_energy += pot_eng;
        // Handle force
        pi.fx -= force_factor*dx;
        pi.fy -= force_factor*dy;
        pi.fz -= force_factor*dz;
        // Use 3d Newton's law
        pj.fx += force_factor*dx;
        pj.fy += force_factor*dy;
        pj.fz += force_factor*dz;
        if (m_system->compute_per_particle_energy())
        {
          pi.add_pot_energy("soft_attractive",pot_eng);
          pj.add_pot_energy("soft_attractive",pot_eng);
        }
      }
    }
  }
}