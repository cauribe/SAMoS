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
 *   (c) 2013, 2014, 2015 
 *   
 *   This program cannot be used, copied, or modified without
 *   explicit permission of the author.
 * 
 * ************************************************************* */

/*!
 * \file constraint_hourglass.hpp
 * \author Rastko Sknepnek, sknepnek@gmail.com
 * \date 09-Feb-2015
 * \brief Declaration of ConstraintHourglass class.
 */ 

#ifndef __CONSTRAINT_HOURGLASS_HPP__
#define __CONSTRAINT_HOURGLASS_HPP__

#include <cmath>

#include "system.hpp"
#include "parse_parameters.hpp"
#include "constraint.hpp"


using std::sqrt;
using std::sin;
using std::cos;
using std::fabs;


/*! Enforces all particles to be on the surface of a period hourglass shaped surface,
 *  i.e., a cylindrical tube whose radius depends on the position along the 
 *  z axis and is assumed to be a sine function.
 *  The surface is given in the implicit for as
 *  \f$ f(x,y,z) = x^2+y^2 - \left(R-A\sin\left\frac {2\pi}{L_z} n z \right)\right) \f$, 
 *  where \f$ R \$ is average tube radius, \f$ A (< R) \f$ is amplitude of the modulation,  \f$ L_z \f$
 *  is the box size in z direction and \f$ n \f$ is number of nodes.
*/
class ConstraintHourglass : public Constraint
{
public:
  
  //! Constructor
  //! \param id unique constraint id
  //! \param sys pointer to the system object
  //! \param msg Pointer to the internal state messenger
  //! \param param parameters that define the manifolds (e.g., sphere radius)
  ConstraintHourglass(SystemPtr sys, MessengerPtr msg, pairs_type& param) : Constraint(sys,msg,param)
  { 
    if (param.find("R") == param.end())
    {
      m_msg->msg(Messenger::WARNING,"Hourglass constraint. Radius has not been set. Assuming 10.0");
      m_R = 10.0;
    }
    else
    {
      m_msg->msg(Messenger::INFO,"Hourglass constraint. Radius set to "+param["R"]+".");
      m_R = lexical_cast<double>(param["R"]);
    }
    if (param.find("A") == param.end())
    {
      m_msg->msg(Messenger::WARNING,"Hourglass constraint. Amplitude has not been set. Assuming 1.0");
      m_A = 1.0;
    }
    else
    {
      m_msg->msg(Messenger::INFO,"Hourglass constraint. Amplitude set to "+param["A"]+".");
      m_A = lexical_cast<double>(param["A"]);
      if (m_A > m_R)
      {
        m_msg->msg(Messenger::ERROR,"Hourglass constraint. Amplitude has to be smaller than the radius.");
        throw runtime_error("Hourglass constraint. Amplitude too large.");
      }
    }
    if (param.find("n") == param.end())
    {
      m_msg->msg(Messenger::WARNING,"Hourglass constraint. Number of nodes not set. Assuming 1.");
      m_n = 1.0;
    }
    else
    {
      m_msg->msg(Messenger::INFO,"Hourglass constraint. Number of nodes set to "+param["n"]+".");
      m_n = lexical_cast<double>(param["n"]);
    }
  }
  
  //! Computes normal to the surface
  void compute_normal(Particle&, double&, double&, double&); 
   
  // Computer gradient at a point
  void compute_gradient(Particle&, double&, double&, double&);
  
  // Value of the constraint
  double constraint_value(Particle&); 
    
private:
  
  double m_R;     //!< Average radius
  double m_A;     //!< Amplitude (< R)
  double m_n;     //!< Number of nodes
  
};

typedef shared_ptr<ConstraintHourglass> ConstraintHourglassPtr;  //!< Shared pointer to the Constraint object

#endif