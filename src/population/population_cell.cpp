/* *************************************************************
 *  
 *   Soft Active Mater on Surfaces (SAMoS)
 *   
 *   Author: Rastko Sknepnek
 *  
 *   Division of Physics
 *   School of Engineering, Physics and Mathematics
 *   University of Dundee
 *   
 *   (c) 2013, 2014
 * 
 *   School of Science and Engineering
 *   School of Life Sciences 
 *   University of Dundee
 * 
 *   (c) 2015
 * 
 *   Author: Silke Henkes
 * 
 *   Department of Physics 
 *   Institute for Complex Systems and Mathematical Biology
 *   University of Aberdeen  
 * 
 *   (c) 2014, 2015
 *  
 *   This program cannot be used, copied, or modified without
 *   explicit written permission of the authors.
 * 
 * ************************************************************* */

/*!
 * \file population_cell.cpp
 * \author Rastko Sknepnek, sknepnek@gmail.com
 * \date 16-Dec-2015
 * \brief Implementation of PopulationCell class.
 */ 

#include "population_cell.hpp"


/*! Divide cells according to their current area.
 *  We draw a uniform random number \f$ \zeta \f$ between 0 and 1
 *  if \f$ \zeta < \exp\left(\gamma(A_i-A_0)\right) \f$, split particle.
 *  Here, \f$ A_i \f$ is current cell area, \f$ A_0 \f$ if the native cell area 
 *  (which changes during growth) and \f$ \gamma \f$ is a constant.  
 * 
 *  After the division, each daughter cell has native area equal to the half of the 
 *  native area of the mother cell. 
 *
 *  Position of daughter cells is determined by the orientation vector n.
 *  \param t current time step
 *  
*/
void PopulationCell::divide(int t)
{
  if (m_freq > 0 && t % m_freq == 0)  // Attempt division only at certain time steps
  { 
    if (!m_system->group_ok(m_group_name))
    {
      cout << "Before divide P: Group info mismatch for group : " << m_group_name << endl;
      throw runtime_error("Group mismatch.");
    }
    Mesh& mesh = m_system->get_mesh();
    int new_type;   // type of new particle
    double new_A0;  // native area of the new cell
    int N = m_system->get_group(m_group_name)->get_size();
    vector<int> particles = m_system->get_group(m_group_name)->get_particles();
    BoxPtr box = m_system->get_box();
    for (int i = 0; i < N; i++)
    {
      int pi = particles[i];
      Particle& p = m_system->get_particle(pi); 
      Vertex& V = mesh.get_vertices()[p.get_id()];
      if ( m_rng->drnd() < exp(m_div_rate*(V.area-p.A0)) )
      {
        Particle p_new(m_system->size(), p.get_type(), p.get_radius());
        p_new.x = p.x + m_alpha*m_split_distance*p.get_radius()*p.nx;
        p_new.y = p.y + m_alpha*m_split_distance*p.get_radius()*p.ny;
        p_new.z = p.z + m_alpha*m_split_distance*p.get_radius()*p.nz;
        p_new.set_parent(p.get_flag());
        m_system->apply_periodic(p_new.x,p_new.y,p_new.z);
        
        p.x -= (1.0-m_alpha)*m_split_distance*p.get_radius()*p.nx;
        p.y -= (1.0-m_alpha)*m_split_distance*p.get_radius()*p.ny;
        p.z -= (1.0-m_alpha)*m_split_distance*p.get_radius()*p.nz;
        p.age = 0.0;
        p.A0 *= 0.5;
        m_system->apply_periodic(p.x,p.y,p.z);
        
        p_new.nx = p.nx; p_new.ny = p.ny; p_new.nz = p.nz;
        p_new.vx = p.vx; p_new.vy = p.vy; p_new.vz = p.vz;
        p_new.Nx = p.Nx; p_new.Ny = p.Ny; p_new.Nz = p.Nz;
        p_new.age = 0.0;
        p_new.A0 = p.A0;
        p_new.set_radius(p.get_radius());
        p_new.set_type(p.get_type());
        for(list<string>::iterator it_g = p.groups.begin(); it_g != p.groups.end(); it_g++)
          p_new.groups.push_back(*it_g);
        m_system->add_particle(p_new);
      }
    }
    if (!m_system->group_ok(m_group_name))
    {
      cout << "After Divide P: Group info mismatch for group : " << m_group_name << endl;
      throw runtime_error("Group mismatch.");
    }
    m_system->set_force_nlist_rebuild(true);
  }
}

/*! Remove particle. 
 * 
 *  In biological systems all cells die. Here we assume that the death is random, but 
 *  proportional to the particles age.
 * 
 *  \param t current time step
 * 
*/
void PopulationCell::remove(int t)
{
  if (m_freq > 0 && t % m_freq == 0 && m_death_rate > 0.0)  // Attempt removal only at certain time steps
  { 
    if (!m_system->group_ok(m_group_name))
    {
      cout << "Before Cell Remove: Group info mismatch for group : " << m_group_name << endl;
      throw runtime_error("Group mismatch.");
    }
    int N = m_system->get_group(m_group_name)->get_size();
    vector<int> particles = m_system->get_group(m_group_name)->get_particles();
    vector<int> to_remove;
    for (int i = 0; i < N; i++)
    {
      int pi = particles[i];
      Particle& p = m_system->get_particle(pi);
      if (m_rng->drnd() < exp(m_death_rate*(p.age-m_max_age)))
          to_remove.push_back(p.get_id());
    }
    int offset = 0;
    for (vector<int>::iterator it = to_remove.begin(); it != to_remove.end(); it++)
    {
      m_system->remove_particle((*it)-offset);
      offset++;      
    }
    if (m_system->size() == 0)
    {
      m_msg->msg(Messenger::ERROR,"Cell population control. No cells left in the system. Please reduce that death rate.");
      throw runtime_error("No cells left in the system.");
    }
    if (!m_system->group_ok(m_group_name))
    {
      cout << "After Cell Remove: Group info mismatch for group : " << m_group_name << endl;
      throw runtime_error("Group mismatch.");
    }
    m_system->set_force_nlist_rebuild(true);
  }
}

/*! Grow (rescale) cell native area by a given amount.
 * 
 *  \param t current time step
 *  
*/
void PopulationCell::grow(int t)
{
  if (m_freq > 0 && t % m_freq == 0 && m_growth_rate > 0.0) 
  { 
    int N = m_system->get_group(m_group_name)->get_size();
    vector<int> particles = m_system->get_group(m_group_name)->get_particles();
    for (int i = 0; i < N; i++)
    {
      int pi = particles[i];
      Particle& p = m_system->get_particle(pi); 
      p.A0 *= (1.0+m_growth_rate);
    }
    m_system->set_force_nlist_rebuild(true);
    //m_system->set_nlist_rescale(m_scale);
  }
}